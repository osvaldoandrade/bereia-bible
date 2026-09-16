"""Deterministic character voice resolution and reference validation."""

from __future__ import annotations

import hashlib
import wave
from pathlib import Path

from .domain import VoiceResolution
from .errors import TTSFailure

_MAX_REFERENCE_BYTES = 32 * 1024 * 1024


def resolve_voices(
    artifact: dict[str, object],
    repository_root: Path,
    narrator_override: Path | None = None,
) -> dict[str, VoiceResolution]:
    """resolve_voices maps every used character through its stable voice ID."""

    bindings = artifact.get("character_bindings")
    if not isinstance(bindings, dict):
        raise TTSFailure("narration artifact has no character bindings")
    voices_dir = repository_root / "voices"
    override = narrator_override.expanduser().resolve() if narrator_override else None
    narrator_path = override or _existing_file(voices_dir / "narrator.wav")
    if narrator_path is None:
        raise TTSFailure(
            "an approved native Brazilian Portuguese narrator reference is required; "
            "provide --voice or voices/narrator.wav"
        )
    _validate_reference_wav(narrator_path)
    resolutions = {}
    for character, voice_value in sorted(bindings.items()):
        if not isinstance(character, str) or not isinstance(voice_value, str):
            raise TTSFailure("narration character binding is invalid")
        requested_path = voices_dir / f"{voice_value}.wav"
        direct_path = narrator_path if character == "narrator" else _existing_file(requested_path)
        if direct_path is not None:
            _validate_reference_wav(direct_path)
            resolutions[character] = _file_resolution(
                character,
                voice_value,
                voice_value if character != "narrator" else "narrator",
                direct_path,
                repository_root,
                fallback=False,
                reason=None,
            )
            continue
        if narrator_path is not None:
            resolutions[character] = _file_resolution(
                character,
                voice_value,
                "narrator",
                narrator_path,
                repository_root,
                fallback=character != "narrator",
                reason=(
                    f"voices/{voice_value}.wav is absent; using narrator reference"
                    if character != "narrator"
                    else None
                ),
            )
            continue
    return resolutions


def _existing_file(path: Path) -> Path | None:
    resolved = path.resolve()
    return resolved if resolved.is_file() else None


def _validate_reference_wav(path: Path) -> None:
    if path.suffix.lower() != ".wav" or not path.is_file():
        raise TTSFailure(f"voice reference must be an existing WAV: {path.name}")
    size = path.stat().st_size
    if size <= 44 or size > _MAX_REFERENCE_BYTES:
        raise TTSFailure(f"voice reference has an invalid size: {path.name}")
    try:
        with wave.open(str(path), "rb") as handle:
            channels = handle.getnchannels()
            sample_width = handle.getsampwidth()
            sample_rate = handle.getframerate()
            frame_count = handle.getnframes()
            compression = handle.getcomptype()
    except (OSError, EOFError, wave.Error) as exc:
        raise TTSFailure(f"voice reference is not a valid PCM WAV: {path.name}") from exc
    duration = frame_count / sample_rate if sample_rate else 0.0
    if compression != "NONE" or channels not in (1, 2) or sample_width != 2:
        raise TTSFailure(f"voice reference must be mono/stereo 16-bit PCM: {path.name}")
    if not 8_000 <= sample_rate <= 96_000 or not 1.0 <= duration <= 30.0:
        raise TTSFailure(f"voice reference must be 1-30 seconds at 8-96 kHz: {path.name}")


def _file_resolution(
    character: str,
    requested: str,
    resolved: str,
    path: Path,
    repository_root: Path,
    *,
    fallback: bool,
    reason: str | None,
) -> VoiceResolution:
    try:
        label = path.relative_to(repository_root.resolve()).as_posix()
    except ValueError:
        label = f"external/{path.name}"
    return VoiceResolution(
        character=character,
        requested_voice_id=requested,
        resolved_voice_id=resolved,
        reference_path=path,
        reference_label=label,
        reference_sha256=_file_sha256(path),
        fallback=fallback,
        fallback_reason=reason,
    )


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
