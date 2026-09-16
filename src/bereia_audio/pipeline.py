"""Chapter-level orchestration, cache reuse, and provenance publication."""

from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

from .bible import BibleRepository
from .cache import (
    MASTERING_PARAMETERS,
    cached_file_matches,
    chapter_fingerprint,
    file_sha256,
    load_json,
    segment_fingerprint,
    tts_identity,
)
from .constants import DEFAULT_SEED, METADATA_SCHEMA_VERSION
from .domain import VoiceResolution
from .mastering import master_chapter, probe_audio
from .narration import analyze_chapter, load_narration_artifact
from .registry import load_registry, write_json_atomic
from .runtime import inspect_environment, validate_host
from .telemetry import emit
from .tts import ChatterboxMLX, Synthesizer
from .voices import resolve_voices


class AudioPipeline:
    """AudioPipeline executes one local, sequential, restartable workflow."""

    def __init__(self, repository_root: Path, synthesizer: Synthesizer | None = None) -> None:
        self.repository_root = repository_root.resolve()
        self.bible = BibleRepository(self.repository_root)
        self.synthesizer = synthesizer or ChatterboxMLX()

    def inspect(self) -> dict[str, object]:
        """inspect validates all local runtime prerequisites without loading weights."""

        report = inspect_environment(include_mlx=True)
        report["repository"] = {
            "root": str(self.repository_root),
            "source_adapter": "translation/*/*/*.json: texto_bv",
        }
        report["tts"] = tts_identity()
        return report

    def analyze(self, book: str, chapter_number: int) -> dict[str, object]:
        """analyze creates one validated and reviewable narration artifact."""

        validate_host()
        run_id = str(uuid.uuid4())
        chapter = self.bible.get_chapter(book, chapter_number)
        paths = chapter_paths(self.repository_root, chapter.book, chapter.number)
        emit("analysis.started", run_id=run_id, book=chapter.book, chapter=chapter.number)
        artifact, duration = analyze_chapter(
            chapter,
            self.repository_root,
            paths["narration"],
        )
        emit(
            "analysis.completed",
            run_id=run_id,
            book=chapter.book,
            chapter=chapter.number,
            segments=len(artifact["segments"]),
            duration_seconds=round(duration, 3),
        )
        return {
            "book": chapter.book,
            "chapter": chapter.number,
            "narration": str(paths["narration"]),
            "segments": len(artifact["segments"]),
            "duration_seconds": round(duration, 3),
        }

    def generate(
        self,
        book: str,
        chapter_number: int,
        *,
        narrator_voice: Path | None = None,
        seed: int = DEFAULT_SEED,
    ) -> dict[str, object]:
        """generate validates, synthesizes, masters, and caches one chapter."""

        runtime_report = inspect_environment(include_mlx=True)
        run_id = str(uuid.uuid4())
        started = time.perf_counter()
        chapter = self.bible.get_chapter(book, chapter_number)
        paths = chapter_paths(self.repository_root, chapter.book, chapter.number)
        narration_path = paths["narration"]
        if not narration_path.is_file():
            self.analyze(chapter.book, chapter.number)
        registry = load_registry(self.repository_root / "character_registry.json")
        narration = load_narration_artifact(narration_path, chapter, registry)
        resolutions = resolve_voices(narration, self.repository_root, narrator_voice)
        voice_metadata = {
            character: resolution.metadata() for character, resolution in resolutions.items()
        }
        fingerprint = chapter_fingerprint(chapter.source_text, narration, voice_metadata, seed)
        cached_metadata = load_json(paths["metadata"])
        if _chapter_cache_matches(paths, cached_metadata, fingerprint):
            emit(
                "generation.cache_hit",
                run_id=run_id,
                book=chapter.book,
                chapter=chapter.number,
                cache_key=fingerprint,
            )
            return _result(paths, chapter.book, chapter.number, fingerprint, cache_hit=True)

        emit(
            "generation.started",
            run_id=run_id,
            book=chapter.book,
            chapter=chapter.number,
            cache_key=fingerprint,
        )
        segment_records, synthesized_seconds = self._generate_segments(
            narration,
            resolutions,
            paths["segments"],
            seed,
            run_id,
        )
        mastering_started = time.perf_counter()
        mastered_segments = [
            (paths["base"] / str(record["path"]), segment)
            for record, segment in zip(segment_records, narration["segments"], strict=True)
        ]
        mastering = master_chapter(
            mastered_segments,
            paths["wav"],
            paths["m4a"],
            title=f"{chapter.book} {chapter.number}",
            album=f"{chapter.book} — Bereia Bible",
            source_commit=chapter.source_commit,
        )
        mastering_seconds = time.perf_counter() - mastering_started
        total_seconds = time.perf_counter() - started
        metadata = _build_metadata(
            chapter=chapter,
            narration=narration,
            resolutions=voice_metadata,
            segment_records=segment_records,
            runtime_report=runtime_report,
            fingerprint=fingerprint,
            seed=seed,
            mastering=mastering,
            synthesized_seconds=synthesized_seconds,
            mastering_seconds=mastering_seconds,
            total_seconds=total_seconds,
        )
        write_json_atomic(paths["metadata"], metadata)
        emit(
            "generation.completed",
            run_id=run_id,
            book=chapter.book,
            chapter=chapter.number,
            duration_seconds=round(mastering.duration_seconds, 3),
            elapsed_seconds=round(total_seconds, 3),
            generated_segments=sum(not bool(item["cache_hit"]) for item in segment_records),
            reused_segments=sum(bool(item["cache_hit"]) for item in segment_records),
        )
        return _result(paths, chapter.book, chapter.number, fingerprint, cache_hit=False)

    def generate_book(
        self,
        book: str,
        *,
        narrator_voice: Path | None = None,
        seed: int = DEFAULT_SEED,
    ) -> list[dict[str, object]]:
        """generate_book processes discovered chapters sequentially and fail-fast."""

        return [
            self.generate(book, chapter, narrator_voice=narrator_voice, seed=seed)
            for chapter in self.bible.list_chapters(book)
        ]

    def _generate_segments(
        self,
        narration: dict[str, object],
        resolutions: dict[str, VoiceResolution],
        segments_dir: Path,
        seed: int,
        run_id: str,
    ) -> tuple[list[dict[str, object]], float]:
        segments_dir.mkdir(parents=True, exist_ok=True)
        records = []
        synthesis_total = 0.0
        for index, segment in enumerate(narration["segments"], start=1):
            character = "narrator" if segment["character"] is None else str(segment["character"])
            resolution = resolutions[character]
            segment_seed = seed + index - 1
            destination = segments_dir / f"{segment['segment_id']}.wav"
            sidecar = segments_dir / f"{segment['segment_id']}.cache.json"
            key = segment_fingerprint(segment, resolution.metadata(), segment_seed)
            cached = load_json(sidecar)
            hit = cached_file_matches(destination, cached, key)
            if hit:
                probe_audio(destination, expected_codec="pcm_s16le")
                metrics_data = cached.get("metrics")
                metrics = metrics_data if isinstance(metrics_data, dict) else {}
            else:
                emit(
                    "segment.started",
                    run_id=run_id,
                    segment_id=segment["segment_id"],
                    verse_start=segment["verse_start"],
                    verse_end=segment["verse_end"],
                    voice_id=resolution.resolved_voice_id,
                )
                measured = self.synthesizer.synthesize(
                    segment, resolution, destination, segment_seed
                )
                probe_audio(destination, expected_codec="pcm_s16le")
                metrics = measured.metadata()
                synthesis_total += measured.processing_seconds
                write_json_atomic(
                    sidecar,
                    {
                        "cache_key": key,
                        "sha256": file_sha256(destination),
                        "seed": segment_seed,
                        "metrics": metrics,
                    },
                )
                emit(
                    "segment.completed",
                    run_id=run_id,
                    segment_id=segment["segment_id"],
                    duration_seconds=metrics["duration_seconds"],
                    processing_seconds=metrics["processing_seconds"],
                )
            records.append(
                {
                    "segment_id": segment["segment_id"],
                    "path": f"segments/{destination.name}",
                    "sha256": file_sha256(destination),
                    "cache_key": key,
                    "cache_hit": hit,
                    "seed": segment_seed,
                    "voice": resolution.metadata(),
                    "metrics": metrics,
                }
            )
        return records, synthesis_total


def chapter_paths(root: Path, book: str, chapter: int) -> dict[str, Path]:
    """chapter_paths returns the stable artifact layout for one coordinate."""

    base = root / "output" / book / f"{chapter:03d}"
    return {
        "base": base,
        "segments": base / "segments",
        "narration": base / "narration.json",
        "metadata": base / "metadata.json",
        "wav": base / "chapter.wav",
        "m4a": base / "chapter.m4a",
    }


def _chapter_cache_matches(
    paths: dict[str, Path], metadata: dict[str, object] | None, fingerprint: str
) -> bool:
    if metadata is None or metadata.get("cache_key") != fingerprint:
        return False
    outputs = metadata.get("outputs")
    if not isinstance(outputs, dict):
        return False
    for label in ("wav", "m4a"):
        details = outputs.get(label)
        path = paths[label]
        if not isinstance(details, dict) or not path.is_file():
            return False
        if details.get("sha256") != file_sha256(path):
            return False
    return True


def _build_metadata(**values: object) -> dict[str, object]:
    chapter = values["chapter"]
    narration = values["narration"]
    mastering = values["mastering"]
    runtime_report = values["runtime_report"]
    segments = values["segment_records"]
    return {
        "schema_version": METADATA_SCHEMA_VERSION,
        "book": chapter.book,
        "chapter": chapter.number,
        "generated_at": datetime.now(UTC).isoformat(),
        "source_commit": chapter.source_commit,
        "narration_source_commit": narration["source_commit"],
        "source_dirty": chapter.source_dirty,
        "source_sha256": narration["source_sha256"],
        "tts_model": tts_identity()["model"],
        "tts_model_revision": tts_identity()["model_revision"],
        "model_revision": tts_identity()["model_revision"],
        "tts_package": tts_identity()["package"],
        "tts_package_version": tts_identity()["package_version"],
        "tts_tokenizer": tts_identity()["tokenizer"],
        "tts_tokenizer_revision": tts_identity()["tokenizer_revision"],
        "runtime": "mps",
        "framework": "mlx",
        "accelerator": "metal",
        "hardware": runtime_report["hardware"]["chip"],
        "hardware_profile": runtime_report["hardware"],
        "narration_model": narration["narration_model"],
        "narration_prompt_version": narration["narration_prompt_version"],
        "narration_schema_version": narration["schema_version"],
        "seed": values["seed"],
        "language": tts_identity()["language"],
        "cache_key": values["fingerprint"],
        "voices": values["resolutions"],
        "segments": segments,
        "mastering": {
            "parameters": MASTERING_PARAMETERS,
            "measured": mastering.loudness,
        },
        "outputs": {
            "wav": {
                "path": "chapter.wav",
                "sha256": mastering.wav_sha256,
                "duration_seconds": round(mastering.duration_seconds, 6),
            },
            "m4a": {
                "path": "chapter.m4a",
                "sha256": mastering.m4a_sha256,
                "duration_seconds": round(mastering.duration_seconds, 6),
            },
        },
        "timings": {
            "synthesis_seconds": round(float(values["synthesized_seconds"]), 6),
            "mastering_seconds": round(float(values["mastering_seconds"]), 6),
            "total_seconds": round(float(values["total_seconds"]), 6),
        },
    }


def _result(
    paths: dict[str, Path], book: str, chapter: int, fingerprint: str, *, cache_hit: bool
) -> dict[str, object]:
    return {
        "book": book,
        "chapter": chapter,
        "cache_hit": cache_hit,
        "cache_key": fingerprint,
        "narration": str(paths["narration"]),
        "metadata": str(paths["metadata"]),
        "wav": str(paths["wav"]),
        "m4a": str(paths["m4a"]),
    }
