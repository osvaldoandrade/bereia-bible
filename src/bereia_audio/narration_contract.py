"""Validation boundary for untrusted narration metadata and saved plans."""

from __future__ import annotations

from .constants import (
    CADENCE_VALUES,
    EMOTION_VALUES,
    LITERARY_TYPE_VALUES,
    NARRATION_SCHEMA_VERSION,
    PITCH_VALUES,
    TONE_VALUES,
)
from .domain import Chapter, SourceUnit
from .errors import NarrationError
from .integrity import (
    build_source_units,
    text_sha256,
    validate_identifier,
    validate_reconstruction,
    validate_unit_groups,
)
from .registry import registry_bindings


def validate_director_result(
    raw: dict[str, object], units: tuple[SourceUnit, ...]
) -> list[dict[str, object]]:
    """validate_director_result treats every LLM field as untrusted input."""

    if set(raw) != {"literary_type", "segments"}:
        raise NarrationError("Codex narration response contains unknown or missing fields")
    if raw.get("literary_type") not in LITERARY_TYPE_VALUES:
        raise NarrationError("Codex returned an unsupported literary_type")
    segments = raw.get("segments")
    if not isinstance(segments, list) or not segments:
        raise NarrationError("Codex narration response requires non-empty segments")
    groups = []
    for index, segment in enumerate(segments, start=1):
        if not isinstance(segment, dict):
            raise NarrationError(f"Codex segment {index} must be an object")
        _validate_director_segment(segment, index)
        groups.append(segment["unit_ids"])
    validate_unit_groups(groups, units)
    _validate_quoted_speakers(segments, units)
    return segments


def validate_narration_artifact(
    artifact: dict[str, object],
    chapter: Chapter,
    registry: dict[str, dict[str, str]],
) -> None:
    """validate_narration_artifact proves schema, binding, coverage, and exact text."""

    _validate_artifact_header(artifact, chapter)
    units = build_source_units(chapter)
    unit_map = {unit.unit_id: unit for unit in units}
    segments = artifact.get("segments")
    if not isinstance(segments, list) or not segments:
        raise NarrationError("narration artifact requires non-empty segments")
    groups: list[list[str]] = []
    reconstructed = []
    for index, segment in enumerate(segments, start=1):
        if not isinstance(segment, dict):
            raise NarrationError(f"narration segment {index} must be an object")
        groups.append(_validate_hydrated_segment(segment, unit_map, registry, index))
        reconstructed.append(str(segment["text"]))
    validate_unit_groups(groups, units)
    validate_reconstruction(chapter.source_text, "".join(reconstructed))
    _validate_bindings(artifact, segments, registry)


def _validate_director_segment(segment: dict[str, object], index: int) -> None:
    required = {
        "unit_ids",
        "speaker",
        "character",
        "voice_id",
        "character_description",
        "tone",
        "emotion",
        "intensity",
        "pace",
        "exaggeration",
        "cfg_weight",
        "temperature",
        "repetition_penalty",
        "min_p",
        "top_p",
        "pause_before_ms",
        "pause_after_ms",
        "prosody",
    }
    if set(segment) != required:
        raise NarrationError(f"Codex segment {index} contains unknown or missing fields")
    unit_ids = segment["unit_ids"]
    if not isinstance(unit_ids, list) or not all(isinstance(item, str) for item in unit_ids):
        raise NarrationError(f"Codex segment {index} has invalid unit_ids")
    _validate_speaker(segment, index)
    _validate_controls(segment, index)


def _validate_speaker(segment: dict[str, object], index: int) -> None:
    speaker = validate_identifier(segment.get("speaker"), "speaker")
    character = segment.get("character")
    if speaker == "narrator":
        if character is not None or segment.get("voice_id") != "narrator":
            raise NarrationError(f"Codex segment {index} has inconsistent narrator metadata")
    else:
        canonical = validate_identifier(character, "character")
        if canonical != speaker:
            raise NarrationError(f"Codex segment {index} speaker must equal character")
        validate_identifier(segment.get("voice_id"), "voice_id")
    description = segment.get("character_description")
    if description is not None and not isinstance(description, str):
        raise NarrationError(f"Codex segment {index} has invalid character_description")


def _validate_controls(segment: dict[str, object], index: int) -> None:
    if segment.get("tone") not in TONE_VALUES or segment.get("emotion") not in EMOTION_VALUES:
        raise NarrationError(f"Codex segment {index} has invalid tone or emotion")
    ranges = {
        "intensity": (0.0, 1.0),
        "pace": (0.75, 1.15),
        "exaggeration": (0.0, 1.0),
        "cfg_weight": (0.0, 1.0),
        "temperature": (0.5, 1.2),
        "repetition_penalty": (1.0, 2.0),
        "min_p": (0.0, 0.2),
        "top_p": (0.5, 1.0),
    }
    for field, bounds in ranges.items():
        _require_number(segment.get(field), field, index, *bounds)
    for field in ("pause_before_ms", "pause_after_ms"):
        value = segment.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 3_000:
            raise NarrationError(f"Codex segment {index} has invalid {field}")
    _validate_prosody(segment.get("prosody"), index)


def _validate_prosody(value: object, index: int) -> None:
    if not isinstance(value, dict) or set(value) != {"pitch", "energy", "cadence"}:
        raise NarrationError(f"Codex segment {index} has invalid prosody")
    if value.get("pitch") not in PITCH_VALUES or value.get("cadence") not in CADENCE_VALUES:
        raise NarrationError(f"Codex segment {index} has unsupported prosody")
    _require_number(value.get("energy"), "prosody.energy", index, 0.0, 1.0)


def _require_number(value: object, field: str, index: int, low: float, high: float) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not low <= value <= high:
        raise NarrationError(f"Codex segment {index} has invalid {field}")


def _validate_quoted_speakers(
    segments: list[dict[str, object]], units: tuple[SourceUnit, ...]
) -> None:
    unit_map = {unit.unit_id: unit for unit in units}
    for segment in segments:
        quoted = any(unit_map[unit_id].quoted for unit_id in segment["unit_ids"])
        unidentified = segment.get("speaker") == "narrator" or segment.get("character") is None
        if quoted and unidentified:
            raise NarrationError("quoted source units require an identified character")


def _validate_artifact_header(artifact: dict[str, object], chapter: Chapter) -> None:
    required = {
        "schema_version",
        "book",
        "chapter",
        "source_commit",
        "source_dirty",
        "source_sha256",
        "source_verses",
        "narration_model",
        "narration_prompt_version",
        "analyzed_at",
        "literary_type",
        "character_registry_sha256_at_analysis",
        "character_bindings",
        "segments",
    }
    if set(artifact) != required:
        raise NarrationError("narration artifact contains unknown or missing top-level fields")
    checks = (
        artifact.get("schema_version") == NARRATION_SCHEMA_VERSION,
        artifact.get("book") == chapter.book,
        artifact.get("chapter") == chapter.number,
        artifact.get("source_sha256") == text_sha256(chapter.source_text),
        artifact.get("literary_type") in LITERARY_TYPE_VALUES,
    )
    if not all(checks):
        raise NarrationError("narration artifact is stale or has an invalid header")
    expected_verses = [
        {"osis": verse.osis, "verse": verse.number, "sha256": verse.source_sha256}
        for verse in chapter.verses
    ]
    if artifact.get("source_verses") != expected_verses:
        raise NarrationError("narration artifact verse provenance is stale")


def _validate_hydrated_segment(
    segment: dict[str, object],
    unit_map: dict[str, SourceUnit],
    registry: dict[str, dict[str, str]],
    index: int,
) -> list[str]:
    expected_fields = {
        "segment_id",
        "unit_ids",
        "verse_start",
        "verse_end",
        "source_start",
        "source_end",
        "text",
        "speaker",
        "character",
        "voice_id",
        "tone",
        "emotion",
        "intensity",
        "pace",
        "exaggeration",
        "cfg_weight",
        "temperature",
        "repetition_penalty",
        "min_p",
        "top_p",
        "pause_before_ms",
        "pause_after_ms",
        "prosody",
    }
    if set(segment) != expected_fields or segment.get("segment_id") != f"s{index:04d}":
        raise NarrationError(f"narration segment {index} has invalid fields or identifier")
    raw = dict(segment)
    raw["character_description"] = None
    final_only = {
        "segment_id",
        "verse_start",
        "verse_end",
        "source_start",
        "source_end",
        "text",
    }
    _validate_director_segment({key: raw[key] for key in raw if key not in final_only}, index)
    unit_ids = segment["unit_ids"]
    if any(unit_id not in unit_map for unit_id in unit_ids):
        raise NarrationError(f"narration segment {index} references an unknown source unit")
    selected = [unit_map[unit_id] for unit_id in unit_ids]
    expected_text = "".join(unit.text for unit in selected)
    expected_bounds = (
        selected[0].verse,
        selected[-1].verse,
        selected[0].source_start,
        selected[-1].source_end,
    )
    actual_bounds = (
        segment["verse_start"],
        segment["verse_end"],
        segment["source_start"],
        segment["source_end"],
    )
    if segment["text"] != expected_text or actual_bounds != expected_bounds:
        raise NarrationError(f"narration segment {index} changed source text or bounds")
    character = "narrator" if segment["character"] is None else str(segment["character"])
    profile = registry.get(character)
    if profile is None or segment["voice_id"] != profile["voice_id"]:
        raise NarrationError(f"narration segment {index} conflicts with character registry")
    return list(unit_ids)


def _validate_bindings(
    artifact: dict[str, object],
    segments: list[dict[str, object]],
    registry: dict[str, dict[str, str]],
) -> None:
    characters = {
        "narrator" if segment["character"] is None else str(segment["character"])
        for segment in segments
    }
    expected = registry_bindings(registry, characters)
    if artifact.get("character_bindings") != expected:
        raise NarrationError("narration character bindings conflict with current registry")
