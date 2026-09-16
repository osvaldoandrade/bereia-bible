"""Persistent character-to-voice registry."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

from .errors import NarrationError
from .integrity import validate_identifier


def load_registry(path: Path) -> dict[str, dict[str, str]]:
    """load_registry validates every persistent character and voice mapping."""

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise NarrationError(f"cannot read character registry {path}: {exc}") from exc
    if not isinstance(value, dict) or "narrator" not in value:
        raise NarrationError("character registry must be an object containing narrator")
    registry: dict[str, dict[str, str]] = {}
    for character, profile in value.items():
        canonical = validate_identifier(character, "character")
        if not isinstance(profile, dict) or set(profile) != {"voice_id", "description"}:
            raise NarrationError(f"invalid registry profile for {character}")
        voice_id = validate_identifier(profile.get("voice_id"), "voice_id")
        description = profile.get("description")
        if not isinstance(description, str) or not description.strip():
            raise NarrationError(f"registry description is empty for {character}")
        registry[canonical] = {"voice_id": voice_id, "description": description.strip()}
    return registry


def ensure_characters(
    registry: dict[str, dict[str, str]],
    raw_segments: list[dict[str, object]],
) -> tuple[dict[str, dict[str, str]], bool]:
    """ensure_characters adds deterministic profiles without remapping existing entries."""

    updated = {character: dict(profile) for character, profile in registry.items()}
    changed = False
    for segment in raw_segments:
        character = segment.get("character")
        if character is None:
            continue
        canonical = validate_identifier(character, "character")
        if canonical in updated:
            continue
        description = segment.get("character_description")
        if not isinstance(description, str) or not description.strip():
            raise NarrationError(f"new character {canonical} requires a description")
        updated[canonical] = {"voice_id": canonical, "description": description.strip()}
        changed = True
    return updated, changed


def registry_bindings(
    registry: dict[str, dict[str, str]],
    characters: set[str],
) -> dict[str, str]:
    """registry_bindings returns the stable voice subset used by one narration plan."""

    bindings = {}
    for character in sorted(characters | {"narrator"}):
        profile = registry.get(character)
        if profile is None:
            raise NarrationError(f"character is absent from registry: {character}")
        bindings[character] = profile["voice_id"]
    return bindings


def registry_sha256(registry: dict[str, dict[str, str]]) -> str:
    """registry_sha256 hashes canonical registry content for provenance."""

    encoded = json.dumps(
        registry,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def write_registry(path: Path, registry: dict[str, dict[str, str]]) -> None:
    """write_registry atomically persists sorted character profiles."""

    ordered = {key: registry[key] for key in sorted(registry)}
    _write_json_atomic(path, ordered)


def write_json_atomic(path: Path, value: object) -> None:
    """write_json_atomic publishes one complete UTF-8 JSON object by rename."""

    _write_json_atomic(path, value)


def canonical_json_sha256(value: object) -> str:
    """canonical_json_sha256 hashes JSON semantics instead of whitespace formatting."""

    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _write_json_atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
