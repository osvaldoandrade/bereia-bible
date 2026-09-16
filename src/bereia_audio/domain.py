"""Immutable values owned by Audio Production."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Verse:
    """Verse is the immutable Audio Production projection of one Bereia record."""

    osis: str
    book: str
    book_name: str
    chapter: int
    number: int
    text: str
    status: str
    source_path: Path
    source_sha256: str


@dataclass(frozen=True, slots=True)
class Chapter:
    """Chapter is an ordered set of source verses from one repository revision."""

    book: str
    osis_book: str
    book_name: str
    number: int
    verses: tuple[Verse, ...]
    source_commit: str
    source_dirty: bool

    @property
    def source_text(self) -> str:
        """source_text joins source records with one narration boundary space."""

        return " ".join(verse.text for verse in self.verses)


@dataclass(frozen=True, slots=True)
class SourceUnit:
    """SourceUnit identifies one contiguous immutable slice of chapter text."""

    unit_id: str
    verse: int
    text: str
    quoted: bool
    source_start: int
    source_end: int


@dataclass(frozen=True, slots=True)
class HardwareProfile:
    """HardwareProfile contains only non-sensitive runtime contract fields."""

    system: str
    machine: str
    model_name: str
    chip: str
    memory_gb: int


@dataclass(frozen=True, slots=True)
class VoiceResolution:
    """VoiceResolution records the deterministic reference selected for a character."""

    character: str
    requested_voice_id: str
    resolved_voice_id: str
    reference_path: Path | None
    reference_label: str | None
    reference_sha256: str
    fallback: bool
    fallback_reason: str | None

    def metadata(self) -> dict[str, object]:
        """metadata returns the path-sanitized representation persisted with audio."""

        return {
            "character": self.character,
            "requested_voice_id": self.requested_voice_id,
            "resolved_voice_id": self.resolved_voice_id,
            "reference_file": self.reference_label,
            "reference_sha256": self.reference_sha256,
            "fallback": self.fallback,
            "fallback_reason": self.fallback_reason,
        }
