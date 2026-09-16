"""Isolated fixtures and fakes for observable audio-pipeline behavior."""

from __future__ import annotations

import json
import math
import struct
import subprocess
import wave
from pathlib import Path

from bereia_audio.domain import Chapter, SourceUnit, VoiceResolution
from bereia_audio.tts import SynthesisMetrics


class ContextDirector:
    """ContextDirector labels quoted units as God and narration as narrator."""

    model = "test-narration-model"

    def run(
        self,
        chapter: Chapter,
        units: tuple[SourceUnit, ...],
        registry: dict[str, dict[str, str]],
    ) -> dict[str, object]:
        del chapter, registry
        return {
            "literary_type": "narrative",
            "segments": [director_segment(unit) for unit in units],
        }


class FakeSynthesizer:
    """FakeSynthesizer writes deterministic PCM without importing Chatterbox."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    def warm_model(self) -> None:
        return None

    def synthesize(
        self,
        segment: dict[str, object],
        voice: VoiceResolution,
        destination: Path,
        seed: int,
    ) -> SynthesisMetrics:
        del voice
        self.calls.append((str(segment["segment_id"]), seed))
        write_test_wav(destination, duration=0.15, frequency=300.0 + seed % 50)
        return SynthesisMetrics(0.15, 0.01, 0.01 / 0.15, 3_600)


def director_segment(unit: SourceUnit, **overrides: object) -> dict[str, object]:
    quoted = unit.quoted
    value: dict[str, object] = {
        "unit_ids": [unit.unit_id],
        "speaker": "god" if quoted else "narrator",
        "character": "god" if quoted else None,
        "voice_id": "god" if quoted else "narrator",
        "character_description": None,
        "tone": "commanding" if quoted else "narrative",
        "emotion": "resolve" if quoted else "neutral",
        "intensity": 0.55 if quoted else 0.3,
        "pace": 0.92,
        "exaggeration": 0.35,
        "cfg_weight": 0.3,
        "temperature": 0.8,
        "repetition_penalty": 1.2,
        "min_p": 0.05,
        "top_p": 1.0,
        "pause_before_ms": 20,
        "pause_after_ms": 30,
        "prosody": {"pitch": "low" if quoted else "neutral", "energy": 0.4, "cadence": "measured"},
    }
    value.update(overrides)
    return value


def make_repository(root: Path) -> Path:
    """make_repository creates a minimal repository-shaped source fixture."""

    chapter_dir = root / "translation" / "01-gn" / "001"
    chapter_dir.mkdir(parents=True)
    (root / "api").mkdir()
    (root / "api" / "verse-record.schema.json").write_text("{}\n", encoding="utf-8")
    records = [
        (1, "Opening narration. “Let there be light.”"),
        (2, "The narration continues."),
    ]
    for number, text in records:
        record = {
            "referencia": {
                "osis": f"Gen.1.{number}",
                "livro": "Gênesis",
                "capitulo": 1,
                "versiculo": number,
            },
            "texto_bv": text,
            "status": "APPROVED",
        }
        (chapter_dir / f"Gen.1.{number}.json").write_text(
            json.dumps(record, ensure_ascii=False), encoding="utf-8"
        )
    (root / "character_registry.json").write_text(
        json.dumps(
            {
                "narrator": {
                    "voice_id": "narrator",
                    "description": "neutral biblical narrator",
                },
                "god": {"voice_id": "god", "description": "controlled and deliberate"},
            }
        ),
        encoding="utf-8",
    )
    write_test_wav(root / "voices/narrator.wav")
    (root / ".gitignore").write_text("output/\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-qm",
            "test fixture",
        ],
        check=True,
    )
    return root


def write_test_wav(
    path: Path,
    *,
    duration: float = 1.2,
    sample_rate: int = 24_000,
    frequency: float = 440.0,
) -> None:
    """write_test_wav creates a small non-silent 16-bit mono PCM fixture."""

    path.parent.mkdir(parents=True, exist_ok=True)
    frame_count = int(duration * sample_rate)
    frames = bytearray()
    for index in range(frame_count):
        value = int(6_000 * math.sin(2 * math.pi * frequency * index / sample_rate))
        frames.extend(struct.pack("<h", value))
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(frames)
