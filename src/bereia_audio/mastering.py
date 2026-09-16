"""Deterministic FFmpeg pacing, pauses, loudness, and chapter encoding."""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .cache import MASTERING_PARAMETERS, file_sha256
from .errors import MasteringError
from .runtime import require_tool


@dataclass(frozen=True, slots=True)
class MasteringResult:
    """MasteringResult describes validated final chapter assets."""

    duration_seconds: float
    wav_sha256: str
    m4a_sha256: str
    loudness: dict[str, str]


def master_chapter(
    segments: list[tuple[Path, dict[str, object]]],
    chapter_wav: Path,
    chapter_m4a: Path,
    *,
    title: str,
    album: str,
    source_commit: str,
) -> MasteringResult:
    """master_chapter applies segment timing then atomically publishes WAV and M4A."""

    if not segments:
        raise MasteringError("cannot master a chapter without segments")
    ffmpeg = require_tool("ffmpeg")
    require_tool("ffprobe")
    chapter_wav.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".mastering-", dir=chapter_wav.parent
    ) as temporary_name:
        work = Path(temporary_name)
        prepared = [
            _prepare_segment(
                ffmpeg,
                source,
                metadata,
                work / f"{index:04d}.wav",
                pause_before_ms=pause_before_ms,
                pause_after_ms=pause_after_ms,
            )
            for index, (source, metadata, pause_before_ms, pause_after_ms) in enumerate(
                _resolve_chapter_pauses(segments), start=1
            )
        ]
        joined = work / "joined.wav"
        _concat_segments(ffmpeg, prepared, joined, work / "segments.ffconcat")
        loudness = _measure_loudness(ffmpeg, joined)
        mastered_wav = work / "chapter.wav"
        _render_master(ffmpeg, joined, mastered_wav, loudness)
        mastered_m4a = work / "chapter.m4a"
        _encode_m4a(
            ffmpeg,
            mastered_wav,
            mastered_m4a,
            title=title,
            album=album,
            source_commit=source_commit,
        )
        duration = probe_audio(mastered_wav, expected_codec="pcm_s16le")
        m4a_duration = probe_audio(mastered_m4a, expected_codec="aac")
        if abs(duration - m4a_duration) > 0.25:
            raise MasteringError("WAV and M4A durations differ unexpectedly")
        wav_hash = file_sha256(mastered_wav)
        m4a_hash = file_sha256(mastered_m4a)
        os.replace(mastered_wav, chapter_wav)
        os.replace(mastered_m4a, chapter_m4a)
    return MasteringResult(duration, wav_hash, m4a_hash, loudness)


def probe_audio(path: Path, *, expected_codec: str | None = None) -> float:
    """probe_audio validates one non-empty, mono generated-audio stream."""

    ffprobe = require_tool("ffprobe")
    process = _run(
        [
            str(ffprobe),
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=codec_name,sample_rate,channels:format=duration",
            "-of",
            "json",
            str(path),
        ],
        timeout=60,
        label="ffprobe",
    )
    try:
        payload = json.loads(process.stdout)
        stream = payload["streams"][0]
        duration = float(payload["format"]["duration"])
        codec = str(stream["codec_name"])
        sample_rate = int(stream["sample_rate"])
        channels = int(stream["channels"])
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise MasteringError(f"generated audio probe is invalid: {path.name}") from exc
    if duration <= 0 or sample_rate != int(MASTERING_PARAMETERS["sample_rate"]) or channels != 1:
        raise MasteringError(
            f"generated audio violates channel or sample-rate contract: {path.name}"
        )
    if expected_codec is not None and codec != expected_codec:
        raise MasteringError(f"generated audio has unexpected codec {codec}: {path.name}")
    return duration


def _prepare_segment(
    ffmpeg: Path,
    source: Path,
    metadata: dict[str, object],
    destination: Path,
    *,
    pause_before_ms: int,
    pause_after_ms: int,
) -> Path:
    pace = float(metadata["pace"])
    filters = [f"atempo={pace:.6f}"]
    if pause_before_ms:
        filters.append(f"adelay=delays={pause_before_ms}:all=1")
    if pause_after_ms:
        filters.append(f"apad=pad_dur={pause_after_ms / 1000:.6f}")
    _run(
        [
            str(ffmpeg),
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-af",
            ",".join(filters),
            "-ar",
            str(MASTERING_PARAMETERS["sample_rate"]),
            "-ac",
            "1",
            "-c:a",
            str(MASTERING_PARAMETERS["wav_codec"]),
            str(destination),
        ],
        timeout=180,
        label=f"segment mastering {source.name}",
    )
    return destination


def _resolve_chapter_pauses(
    segments: list[tuple[Path, dict[str, object]]],
) -> list[tuple[Path, dict[str, object], int, int]]:
    """Resolve each boundary to one pause instead of stacking both sides."""

    resolved: list[tuple[Path, dict[str, object], int, int]] = []
    last_index = len(segments) - 1
    for index, (source, metadata) in enumerate(segments):
        before = int(metadata["pause_before_ms"]) if index == 0 else 0
        if index == last_index:
            after = int(metadata["pause_after_ms"])
        else:
            next_metadata = segments[index + 1][1]
            after = max(
                int(metadata["pause_after_ms"]),
                int(next_metadata["pause_before_ms"]),
            )
        resolved.append((source, metadata, before, after))
    return resolved


def _concat_segments(ffmpeg: Path, sources: list[Path], destination: Path, manifest: Path) -> None:
    lines = [f"file '{_ffconcat_escape(path.resolve())}'" for path in sources]
    manifest.write_text("ffconcat version 1.0\n" + "\n".join(lines) + "\n", encoding="utf-8")
    _run(
        [
            str(ffmpeg),
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(manifest),
            "-c:a",
            str(MASTERING_PARAMETERS["wav_codec"]),
            str(destination),
        ],
        timeout=600,
        label="chapter concatenation",
    )


def _measure_loudness(ffmpeg: Path, source: Path) -> dict[str, str]:
    loudnorm = _loudnorm_prefix() + ":print_format=json"
    process = _run(
        [
            str(ffmpeg),
            "-nostdin",
            "-hide_banner",
            "-i",
            str(source),
            "-af",
            loudnorm,
            "-f",
            "null",
            "-",
        ],
        timeout=600,
        label="loudness measurement",
    )
    matches = re.findall(r"\{\s*\"input_i\".*?\}", process.stderr, flags=re.DOTALL)
    if not matches:
        raise MasteringError("FFmpeg did not return loudness measurements")
    try:
        values = json.loads(matches[-1])
        return {
            name: str(values[name])
            for name in ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")
        }
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise MasteringError("FFmpeg returned invalid loudness measurements") from exc


def _render_master(
    ffmpeg: Path,
    source: Path,
    destination: Path,
    measured: dict[str, str],
) -> None:
    loudnorm = (
        _loudnorm_prefix()
        + f":measured_I={measured['input_i']}"
        + f":measured_TP={measured['input_tp']}"
        + f":measured_LRA={measured['input_lra']}"
        + f":measured_thresh={measured['input_thresh']}"
        + f":offset={measured['target_offset']}:linear=true:print_format=summary"
    )
    _run(
        [
            str(ffmpeg),
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-af",
            loudnorm,
            "-ar",
            str(MASTERING_PARAMETERS["sample_rate"]),
            "-ac",
            "1",
            "-c:a",
            str(MASTERING_PARAMETERS["wav_codec"]),
            str(destination),
        ],
        timeout=900,
        label="chapter loudness mastering",
    )


def _encode_m4a(
    ffmpeg: Path,
    source: Path,
    destination: Path,
    *,
    title: str,
    album: str,
    source_commit: str,
) -> None:
    _run(
        [
            str(ffmpeg),
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-c:a",
            str(MASTERING_PARAMETERS["m4a_codec"]),
            "-b:a",
            str(MASTERING_PARAMETERS["m4a_bitrate"]),
            "-ar",
            str(MASTERING_PARAMETERS["sample_rate"]),
            "-ac",
            "1",
            "-metadata",
            f"title={title}",
            "-metadata",
            f"album={album}",
            "-metadata",
            "artist=Bereia Bible",
            "-metadata",
            f"comment=Source commit {source_commit}",
            str(destination),
        ],
        timeout=600,
        label="M4A encoding",
    )


def _loudnorm_prefix() -> str:
    return (
        f"loudnorm=I={MASTERING_PARAMETERS['loudness_lufs']}"
        f":LRA={MASTERING_PARAMETERS['loudness_range']}"
        f":TP={MASTERING_PARAMETERS['true_peak_db']}"
    )


def _run(command: list[str], *, timeout: int, label: str) -> subprocess.CompletedProcess[str]:
    try:
        process = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise MasteringError(f"{label} failed to execute") from exc
    if process.returncode != 0:
        detail = process.stderr.strip().splitlines()
        suffix = f": {detail[-1][:240]}" if detail else ""
        raise MasteringError(f"{label} failed with exit code {process.returncode}{suffix}")
    return process


def _ffconcat_escape(path: Path) -> str:
    return str(path).replace("'", "'\\''")
