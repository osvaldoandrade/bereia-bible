"""Codex narration director and exact-source artifact hydration."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from .constants import (
    DEFAULT_NARRATION_MODEL,
    NARRATION_PROMPT_VERSION,
    NARRATION_SCHEMA_VERSION,
)
from .domain import Chapter, SourceUnit
from .errors import NarrationError, RuntimeContractError
from .integrity import build_source_units, text_sha256
from .narration_contract import validate_director_result, validate_narration_artifact
from .registry import (
    ensure_characters,
    load_registry,
    registry_bindings,
    registry_sha256,
    write_json_atomic,
    write_registry,
)


class DirectorRunner(Protocol):
    """DirectorRunner supplies untrusted narration metadata for one chapter."""

    model: str

    def run(
        self,
        chapter: Chapter,
        units: tuple[SourceUnit, ...],
        registry: dict[str, dict[str, str]],
    ) -> dict[str, object]:
        """run asks a narration model for metadata without authoritative text."""


class CodexDirector:
    """CodexDirector invokes the authenticated local Codex CLI in a read-only sandbox."""

    def __init__(self, repository_root: Path, model: str | None = None, timeout: int = 900) -> None:
        self.repository_root = repository_root
        self.model = model or detect_codex_model()
        self.timeout = timeout

    def run(
        self,
        chapter: Chapter,
        units: tuple[SourceUnit, ...],
        registry: dict[str, dict[str, str]],
    ) -> dict[str, object]:
        """run returns schema-constrained metadata from an isolated Codex process."""

        executable = shutil.which("codex")
        if executable is None:
            raise RuntimeContractError("codex CLI is required for narration analysis")
        schema_path = self.repository_root / "api" / "narration-director.schema.json"
        prompt = _director_prompt(chapter, units, registry)
        try:
            return self._execute(executable, schema_path, prompt)
        except subprocess.TimeoutExpired as exc:
            raise NarrationError(
                f"Codex narration analysis exceeded {self.timeout} seconds"
            ) from exc

    def _execute(self, executable: str, schema_path: Path, prompt: str) -> dict[str, object]:
        with tempfile.TemporaryDirectory(prefix="bereia-audio-director-") as temporary_dir:
            result_path = Path(temporary_dir) / "result.json"
            command = [
                executable,
                "exec",
                "--ephemeral",
                "--ignore-user-config",
                "--ignore-rules",
                "--sandbox",
                "read-only",
                "--skip-git-repo-check",
                "--model",
                self.model,
                "--output-schema",
                str(schema_path),
                "--output-last-message",
                str(result_path),
                "-C",
                temporary_dir,
                "-",
            ]
            process = subprocess.run(
                command,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            if process.returncode != 0:
                raise NarrationError(
                    f"Codex narration analysis failed with exit code {process.returncode}"
                )
            return _read_director_result(result_path)


def analyze_chapter(
    chapter: Chapter,
    repository_root: Path,
    output_path: Path,
    runner: DirectorRunner | None = None,
) -> tuple[dict[str, object], float]:
    """analyze_chapter creates a validated source-hydrated narration artifact."""

    units = build_source_units(chapter)
    registry_path = repository_root / "character_registry.json"
    registry = load_registry(registry_path)
    selected_runner = runner or CodexDirector(repository_root)
    started = time.perf_counter()
    raw = selected_runner.run(chapter, units, registry)
    duration = time.perf_counter() - started
    raw_segments = validate_director_result(raw, units)
    updated_registry, changed = ensure_characters(registry, raw_segments)
    artifact = _hydrate_artifact(chapter, units, raw, updated_registry, selected_runner.model)
    validate_narration_artifact(artifact, chapter, updated_registry)
    if changed:
        write_registry(registry_path, updated_registry)
    write_json_atomic(output_path, artifact)
    return artifact, duration


def load_narration_artifact(
    path: Path,
    chapter: Chapter,
    registry: dict[str, dict[str, str]],
) -> dict[str, object]:
    """load_narration_artifact reads and revalidates a reviewable narration plan."""

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise NarrationError(f"cannot read narration artifact {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise NarrationError("narration artifact must be a JSON object")
    validate_narration_artifact(value, chapter, registry)
    return value


def detect_codex_model() -> str:
    """detect_codex_model resolves a non-secret model name from environment or Codex config."""

    configured = os.environ.get("BEREIA_NARRATION_MODEL")
    if configured:
        return configured
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    config_path = codex_home / "config.toml"
    try:
        value = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError):
        return DEFAULT_NARRATION_MODEL
    model = value.get("model")
    return model if isinstance(model, str) and model else DEFAULT_NARRATION_MODEL


def _director_prompt(
    chapter: Chapter,
    units: tuple[SourceUnit, ...],
    registry: dict[str, dict[str, str]],
) -> str:
    payload = {
        "book": chapter.book,
        "chapter": chapter.number,
        "verses": [{"verse": verse.number, "text": verse.text} for verse in chapter.verses],
        "units": [
            {
                "unit_id": unit.unit_id,
                "verse": unit.verse,
                "quoted": unit.quoted,
                "text": unit.text,
            }
            for unit in units
        ],
        "character_registry": registry,
    }
    rules = """
You are the narration director for a restrained Portuguese biblical audiobook.
Analyze the complete chapter and return narration metadata only. Never rewrite,
correct, translate, summarize, expand, omit, or repeat biblical text.

Group the supplied immutable units into smaller TTS segments. Use every unit_id
exactly once, in the supplied order, and keep each group contiguous. The
application will copy text from those IDs; you do not return text.

Identify direct speech and its character from chapter context. A quoted unit is
a structural clue, but you must determine who speaks. Use speaker="narrator"
and character=null for narration. For a character, set speaker and character to
the same canonical lowercase English identifier, such as god, adam, eve, or
serpent. Reuse registry identifiers and voice_id values. For a new character,
use a stable canonical identifier for both character and voice_id and provide a
short English character_description.

Choose audiobook-like tone, emotion, intensity, pace, pauses, and supported
Chatterbox controls. Keep delivery controlled and non-theatrical. Prosody
describes pitch, energy, and cadence; it never adds spoken words.
""".strip()
    return f"{rules}\n\nINPUT JSON:\n{json.dumps(payload, ensure_ascii=False)}"


def _read_director_result(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise NarrationError("Codex did not produce valid narration JSON") from exc
    if not isinstance(value, dict):
        raise NarrationError("Codex narration response must be a JSON object")
    return value


def _hydrate_artifact(
    chapter: Chapter,
    units: tuple[SourceUnit, ...],
    raw: dict[str, object],
    registry: dict[str, dict[str, str]],
    model: str,
) -> dict[str, object]:
    unit_map = {unit.unit_id: unit for unit in units}
    characters = {
        str(segment["character"])
        for segment in raw["segments"]
        if segment.get("character") is not None
    }
    bindings = registry_bindings(registry, characters)
    segments = [
        _hydrate_segment(index, segment, unit_map, bindings)
        for index, segment in enumerate(raw["segments"], start=1)
    ]
    return {
        "schema_version": NARRATION_SCHEMA_VERSION,
        "book": chapter.book,
        "chapter": chapter.number,
        "source_commit": chapter.source_commit,
        "source_dirty": chapter.source_dirty,
        "source_sha256": text_sha256(chapter.source_text),
        "source_verses": [
            {"osis": verse.osis, "verse": verse.number, "sha256": verse.source_sha256}
            for verse in chapter.verses
        ],
        "narration_model": model,
        "narration_prompt_version": NARRATION_PROMPT_VERSION,
        "analyzed_at": datetime.now(UTC).isoformat(),
        "literary_type": raw["literary_type"],
        "character_registry_sha256_at_analysis": registry_sha256(registry),
        "character_bindings": bindings,
        "segments": segments,
    }


def _hydrate_segment(
    index: int,
    raw: dict[str, object],
    unit_map: dict[str, SourceUnit],
    bindings: dict[str, str],
) -> dict[str, object]:
    selected = [unit_map[unit_id] for unit_id in raw["unit_ids"]]
    character = raw["character"]
    binding_key = "narrator" if character is None else str(character)
    hydrated = dict(raw)
    hydrated.pop("character_description")
    hydrated.update(
        {
            "segment_id": f"s{index:04d}",
            "verse_start": selected[0].verse,
            "verse_end": selected[-1].verse,
            "source_start": selected[0].source_start,
            "source_end": selected[-1].source_end,
            "text": "".join(unit.text for unit in selected),
            "voice_id": bindings[binding_key],
        }
    )
    ordered_fields = (
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
    )
    return {field: hydrated[field] for field in ordered_fields}
