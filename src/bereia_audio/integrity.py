"""Source-unit construction and text-integrity validation."""

from __future__ import annotations

import hashlib
import re
import unicodedata

from .domain import Chapter, SourceUnit
from .errors import NarrationError

_OPEN_QUOTES = frozenset({"“", "«"})
_CLOSE_QUOTES = frozenset({"”", "»"})


def normalize(text: str) -> str:
    """normalize applies Unicode compatibility and whitespace normalization only."""

    return " ".join(unicodedata.normalize("NFKC", text).split())


def text_sha256(text: str) -> str:
    """text_sha256 hashes UTF-8 source text for artifact provenance."""

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_source_units(chapter: Chapter) -> tuple[SourceUnit, ...]:
    """build_source_units partitions chapter text at verse and quotation boundaries."""

    units: list[SourceUnit] = []
    offset = 0
    quoted = False
    total_verses = len(chapter.verses)
    for verse_index, verse in enumerate(chapter.verses):
        suffix = " " if verse_index + 1 < total_verses else ""
        chunks, quoted = _split_quoted(verse.text + suffix, quoted)
        for chunk, chunk_quoted in chunks:
            unit_id = f"u{len(units) + 1:04d}"
            units.append(
                SourceUnit(
                    unit_id=unit_id,
                    verse=verse.number,
                    text=chunk,
                    quoted=chunk_quoted,
                    source_start=offset,
                    source_end=offset + len(chunk),
                )
            )
            offset += len(chunk)
    reconstructed = "".join(unit.text for unit in units)
    if reconstructed != chapter.source_text:
        raise NarrationError("source-unit partition changed chapter text")
    return tuple(units)


def validate_unit_groups(
    segment_groups: list[list[str]],
    units: tuple[SourceUnit, ...],
) -> None:
    """validate_unit_groups proves complete, unique, ordered source coverage."""

    expected = [unit.unit_id for unit in units]
    actual = [unit_id for group in segment_groups for unit_id in group]
    if any(not group for group in segment_groups):
        raise NarrationError("every narration segment must contain source units")
    if actual != expected:
        raise NarrationError("narration units must cover the chapter exactly once in source order")


def validate_reconstruction(source_text: str, reconstructed: str) -> None:
    """validate_reconstruction rejects exact or normalized textual divergence."""

    if reconstructed != source_text:
        raise NarrationError("narration segments do not exactly reconstruct source text")
    if normalize(source_text) != normalize(reconstructed):
        raise NarrationError("normalized narration reconstruction differs from source text")


def validate_identifier(value: object, field: str) -> str:
    """validate_identifier accepts stable lowercase character and voice identifiers."""

    if not isinstance(value, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", value):
        raise NarrationError(f"{field} must be a canonical lowercase identifier")
    return value


def _split_quoted(text: str, initial_quoted: bool) -> tuple[list[tuple[str, bool]], bool]:
    chunks: list[tuple[str, bool]] = []
    start = 0
    quoted = initial_quoted
    for index, character in enumerate(text):
        if character in _OPEN_QUOTES and not quoted:
            _append_chunk(chunks, text[start:index], False)
            start = index
            quoted = True
        elif character in _CLOSE_QUOTES and quoted:
            _append_chunk(chunks, text[start : index + 1], True)
            start = index + 1
            quoted = False
        elif character == '"':
            if quoted:
                _append_chunk(chunks, text[start : index + 1], True)
                start = index + 1
            else:
                _append_chunk(chunks, text[start:index], False)
                start = index
            quoted = not quoted
    _append_chunk(chunks, text[start:], quoted)
    return chunks, quoted


def _append_chunk(chunks: list[tuple[str, bool]], text: str, quoted: bool) -> None:
    if text:
        chunks.append((text, quoted))
