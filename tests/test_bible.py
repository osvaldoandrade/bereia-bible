"""Observable contracts for the repository-owned Bible adapter."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bereia_audio import bible
from bereia_audio.bible import BibleRepository
from bereia_audio.errors import SourceError
from tests.support import make_repository


class BibleRepositoryTests(unittest.TestCase):
    def test_real_genesis_chapter_reads_repository_text(self) -> None:
        chapter = bible.get_chapter("GEN", 1)

        self.assertEqual((chapter.book, chapter.number, len(chapter.verses)), ("GEN", 1, 31))
        self.assertEqual(chapter.verses[0].source_path.name, "Gen.1.1.json")
        self.assertTrue(all(verse.text for verse in chapter.verses))

    def test_real_genesis_verses_are_numeric_order(self) -> None:
        chapter = bible.get_chapter("Gênesis", 1)

        self.assertEqual([verse.number for verse in chapter.verses], list(range(1, 32)))

    def test_aliases_resolve_to_canonical_osis_book(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = make_repository(Path(temporary))
            repository = BibleRepository(root)

            self.assertEqual(repository.get_chapter("gn", 1).book, "GEN")
            self.assertEqual(repository.get_chapter("Gênesis", 1).book, "GEN")

    def test_list_chapters_uses_numeric_directories_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = make_repository(Path(temporary))
            extra = root / "translation" / "01-gn" / "notes"
            extra.mkdir()
            (extra / "ignored.json").write_text("{}", encoding="utf-8")

            self.assertEqual(BibleRepository(root).list_chapters("GEN"), (1,))

    def test_unknown_book_fails(self) -> None:
        with self.assertRaisesRegex(SourceError, "unknown or ambiguous"):
            bible.get_chapter("UNKNOWN", 1)

    def test_non_positive_chapter_fails(self) -> None:
        with self.assertRaisesRegex(SourceError, "positive integer"):
            bible.get_chapter("GEN", 0)

    def test_duplicate_verse_number_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = make_repository(Path(temporary))
            original = root / "translation/01-gn/001/Gen.1.2.json"
            record = json.loads(original.read_text(encoding="utf-8"))
            record["referencia"]["versiculo"] = 1
            original.write_text(json.dumps(record), encoding="utf-8")

            with self.assertRaisesRegex(SourceError, "positive and unique"):
                BibleRepository(root).get_chapter("GEN", 1)

    def test_empty_source_text_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = make_repository(Path(temporary))
            path = root / "translation/01-gn/001/Gen.1.1.json"
            record = json.loads(path.read_text(encoding="utf-8"))
            record["texto_bv"] = " "
            path.write_text(json.dumps(record), encoding="utf-8")

            with self.assertRaisesRegex(SourceError, "empty texto_bv"):
                BibleRepository(root).get_chapter("GEN", 1)


if __name__ == "__main__":
    unittest.main()
