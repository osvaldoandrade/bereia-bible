"""Read-only adapter for repository-owned Bereia verse records."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from .domain import Chapter, Verse
from .errors import SourceError


@dataclass(frozen=True, slots=True)
class _BookLocation:
    directory: Path
    osis_book: str
    book_name: str
    aliases: frozenset[str]


class BibleRepository:
    """BibleRepository reads `texto_bv` without mutating the source repository."""

    def __init__(self, root: Path | str | None = None) -> None:
        self.root = find_repository_root(root)
        self._books = self._discover_books()

    def get_chapter(self, book: str, chapter: int) -> Chapter:
        """get_chapter reads and validates one chapter in numeric verse order."""

        if not isinstance(chapter, int) or isinstance(chapter, bool) or chapter < 1:
            raise SourceError(f"chapter must be a positive integer: {chapter!r}")
        location = self._resolve_book(book)
        chapter_dir = location.directory / f"{chapter:03d}"
        record_paths = sorted(chapter_dir.glob("*.json"))
        if not record_paths:
            raise SourceError(f"Bereia chapter not found: {book.upper()} {chapter}")
        verses = tuple(self._read_verse(path, location, chapter) for path in record_paths)
        verses = tuple(sorted(verses, key=lambda verse: verse.number))
        self._validate_verse_order(verses)
        commit, dirty = self._git_state()
        return Chapter(
            book=_canonical_book(location.osis_book),
            osis_book=location.osis_book,
            book_name=location.book_name,
            number=chapter,
            verses=verses,
            source_commit=commit,
            source_dirty=dirty,
        )

    def list_chapters(self, book: str) -> tuple[int, ...]:
        """list_chapters returns chapter numbers discovered from repository directories."""

        location = self._resolve_book(book)
        chapters = []
        for candidate in location.directory.iterdir():
            if (
                candidate.is_dir()
                and re.fullmatch(r"\d{3}", candidate.name)
                and any(candidate.glob("*.json"))
            ):
                chapters.append(int(candidate.name))
        if not chapters:
            raise SourceError(f"no Bereia chapters found for {book!r}")
        return tuple(sorted(chapters))

    def _discover_books(self) -> tuple[_BookLocation, ...]:
        locations = []
        for directory in sorted((self.root / "translation").glob("[0-9][0-9]-*")):
            sample_path = next(iter(sorted(directory.glob("[0-9][0-9][0-9]/*.json"))), None)
            if sample_path is None:
                continue
            record = _read_json(sample_path)
            reference = _require_mapping(record, "referencia", sample_path)
            osis = _require_string(reference, "osis", sample_path)
            book_name = _require_string(reference, "livro", sample_path)
            osis_book = osis.split(".", 1)[0]
            suffix = directory.name.split("-", 1)[-1]
            aliases = frozenset(
                {_canonical_book(osis_book), _canonical_book(book_name), _canonical_book(suffix)}
            )
            locations.append(_BookLocation(directory, osis_book, book_name, aliases))
        if not locations:
            raise SourceError(f"no Bereia translation books found under {self.root}")
        return tuple(locations)

    def _resolve_book(self, book: str) -> _BookLocation:
        wanted = _canonical_book(book)
        matches = [location for location in self._books if wanted in location.aliases]
        if len(matches) != 1:
            raise SourceError(f"Bereia book identifier is unknown or ambiguous: {book!r}")
        return matches[0]

    def _read_verse(self, path: Path, location: _BookLocation, chapter: int) -> Verse:
        record = _read_json(path)
        reference = _require_mapping(record, "referencia", path)
        osis = _require_string(reference, "osis", path)
        book_name = _require_string(reference, "livro", path)
        record_chapter = _require_integer(reference, "capitulo", path)
        number = _require_integer(reference, "versiculo", path)
        text = _require_string(record, "texto_bv", path)
        status = _require_string(record, "status", path)
        if record_chapter != chapter or not osis.startswith(f"{location.osis_book}.{chapter}."):
            raise SourceError(f"cross-chapter record at {path}")
        if book_name != location.book_name or not text.strip():
            raise SourceError(f"invalid Bereia verse identity or empty texto_bv at {path}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return Verse(
            osis=osis,
            book=_canonical_book(location.osis_book),
            book_name=book_name,
            chapter=chapter,
            number=number,
            text=text,
            status=status,
            source_path=path,
            source_sha256=digest,
        )

    def _validate_verse_order(self, verses: tuple[Verse, ...]) -> None:
        numbers = [verse.number for verse in verses]
        if any(number < 1 for number in numbers) or len(numbers) != len(set(numbers)):
            raise SourceError("verse numbers must be positive and unique")
        if numbers != sorted(numbers):
            raise SourceError("verse records are not in numeric order")

    def _git_state(self) -> tuple[str, bool]:
        commit = _run_git(self.root, "rev-parse", "HEAD")
        dirty = bool(_run_git(self.root, "status", "--porcelain=v1"))
        return commit, dirty


def get_chapter(
    book: str,
    chapter: int,
    repository_root: Path | str | None = None,
) -> Chapter:
    """get_chapter exposes the required adapter call with a discovered repository root."""

    return BibleRepository(repository_root).get_chapter(book, chapter)


def find_repository_root(start: Path | str | None = None) -> Path:
    """find_repository_root locates the checked-out Bereia source contract."""

    configured = os.environ.get("BEREIA_BIBLE_ROOT")
    initial = Path(start or configured or Path.cwd()).expanduser().resolve()
    candidates = (initial, *initial.parents)
    for candidate in candidates:
        if (candidate / "translation").is_dir() and (
            candidate / "api" / "verse-record.schema.json"
        ).is_file():
            return candidate
    raise SourceError(f"not inside a bereia-bible checkout: {initial}")


def _canonical_book(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SourceError("book must be a non-empty string")
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_value = decomposed.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^A-Z0-9]", "", ascii_value.upper())


def _read_json(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SourceError(f"cannot read Bereia record {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SourceError(f"Bereia record must be a JSON object: {path}")
    return value


def _require_mapping(record: dict[str, object], key: str, path: Path) -> dict[str, object]:
    value = record.get(key)
    if not isinstance(value, dict):
        raise SourceError(f"{path}: {key} must be an object")
    return value


def _require_string(record: dict[str, object], key: str, path: Path) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value:
        raise SourceError(f"{path}: {key} must be a non-empty string")
    return value


def _require_integer(record: dict[str, object], key: str, path: Path) -> int:
    value = record.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise SourceError(f"{path}: {key} must be a positive integer")
    return value


def _run_git(root: Path, *args: str) -> str:
    try:
        process = subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise SourceError(f"cannot inspect Bereia source revision: {exc}") from exc
    return process.stdout.strip()
