"""Content-addressed cache keys and generated-file verification."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .constants import (
    METADATA_SCHEMA_VERSION,
    PACKAGE_VERSION,
    TTS_LANGUAGE,
    TTS_MODEL,
    TTS_MODEL_REVISION,
    TTS_PACKAGE,
    TTS_PACKAGE_VERSION,
    TTS_TOKENIZER,
    TTS_TOKENIZER_REVISION,
)
from .registry import canonical_json_sha256

MASTERING_PARAMETERS = {
    "sample_rate": 24_000,
    "channels": 1,
    "wav_codec": "pcm_s16le",
    "m4a_codec": "aac",
    "m4a_bitrate": "128k",
    "loudness_lufs": -18.0,
    "loudness_range": 7.0,
    "true_peak_db": -1.5,
}


def chapter_fingerprint(
    source_text: str,
    narration: dict[str, object],
    voices: dict[str, object],
    seed: int,
) -> str:
    """chapter_fingerprint covers every authoritative generation input."""

    return canonical_json_sha256(
        {
            "source_text": source_text,
            "narration": narration,
            "voices": voices,
            "tts": tts_identity(),
            "pipeline": {
                "package_version": PACKAGE_VERSION,
                "metadata_schema_version": METADATA_SCHEMA_VERSION,
            },
            "seed": seed,
            "mastering": MASTERING_PARAMETERS,
        }
    )


def segment_fingerprint(
    segment: dict[str, object],
    voice: dict[str, object],
    seed: int,
) -> str:
    """segment_fingerprint narrows the generation identity to one segment."""

    return canonical_json_sha256(
        {"segment": segment, "voice": voice, "tts": tts_identity(), "seed": seed}
    )


def tts_identity() -> dict[str, object]:
    """tts_identity returns immutable package and weight provenance."""

    return {
        "package": TTS_PACKAGE,
        "package_version": TTS_PACKAGE_VERSION,
        "model": TTS_MODEL,
        "model_revision": TTS_MODEL_REVISION,
        "tokenizer": TTS_TOKENIZER,
        "tokenizer_revision": TTS_TOKENIZER_REVISION,
        "language": TTS_LANGUAGE,
        "max_new_tokens": 1_000,
    }


def file_sha256(path: Path) -> str:
    """file_sha256 hashes a generated artifact without loading it into memory."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, object] | None:
    """load_json returns None for absent, malformed, or non-object cache data."""

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def cached_file_matches(path: Path, cache: dict[str, object] | None, key: str) -> bool:
    """cached_file_matches verifies both key and bytes before reuse."""

    if cache is None or cache.get("cache_key") != key or not path.is_file():
        return False
    expected = cache.get("sha256")
    return isinstance(expected, str) and expected == file_sha256(path)
