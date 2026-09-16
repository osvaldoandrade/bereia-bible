"""Text preservation and source-unit properties."""

from __future__ import annotations

import random
import string
import unittest
from itertools import pairwise

from bereia_audio import bible
from bereia_audio.errors import NarrationError
from bereia_audio.integrity import (
    build_source_units,
    normalize,
    validate_identifier,
    validate_reconstruction,
    validate_unit_groups,
)


class IntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.chapter = bible.get_chapter("GEN", 1)
        cls.units = build_source_units(cls.chapter)

    def test_source_units_exactly_reconstruct_genesis(self) -> None:
        self.assertEqual("".join(unit.text for unit in self.units), self.chapter.source_text)

    def test_source_unit_offsets_are_contiguous(self) -> None:
        bounds = [(unit.source_start, unit.source_end) for unit in self.units]

        self.assertEqual(bounds[0][0], 0)
        self.assertEqual(bounds[-1][1], len(self.chapter.source_text))
        self.assertTrue(all(left[1] == right[0] for left, right in pairwise(bounds)))

    def test_quote_state_continues_across_verses(self) -> None:
        verse_29_30 = [unit for unit in self.units if unit.verse in (29, 30)]

        quoted = [unit for unit in verse_29_30 if unit.quoted]
        self.assertEqual([unit.verse for unit in quoted], [29, 30])

    def test_complete_ordered_groups_pass(self) -> None:
        validate_unit_groups([[unit.unit_id] for unit in self.units], self.units)

    def test_reordered_groups_fail(self) -> None:
        groups = [[unit.unit_id] for unit in self.units]
        groups[0], groups[1] = groups[1], groups[0]

        with self.assertRaisesRegex(NarrationError, "exactly once"):
            validate_unit_groups(groups, self.units)

    def test_omitted_group_fails(self) -> None:
        groups = [[unit.unit_id] for unit in self.units[:-1]]

        with self.assertRaisesRegex(NarrationError, "exactly once"):
            validate_unit_groups(groups, self.units)

    def test_empty_group_fails(self) -> None:
        groups = [[unit.unit_id] for unit in self.units]
        groups.insert(1, [])

        with self.assertRaisesRegex(NarrationError, "contain source units"):
            validate_unit_groups(groups, self.units)

    def test_exact_reconstruction_rejects_whitespace_change(self) -> None:
        with self.assertRaisesRegex(NarrationError, "exactly reconstruct"):
            validate_reconstruction(self.chapter.source_text, self.chapter.source_text + " ")

    def test_normalize_is_idempotent_for_random_unicode_safe_text(self) -> None:
        generator = random.Random(1234)
        alphabet = string.ascii_letters + " áéíóú\t\n"
        for _ in range(500):
            value = "".join(generator.choice(alphabet) for _ in range(generator.randrange(80)))
            self.assertEqual(normalize(normalize(value)), normalize(value))

    def test_identifier_accepts_and_rejects_boundaries(self) -> None:
        accepted = ["a", "narrator", "character_1", "voice-id"]
        rejected = ["", "God", "1voice", "a" * 65, "../voice"]
        for value in accepted:
            with self.subTest(value=value):
                self.assertEqual(validate_identifier(value, "id"), value)
        for value in rejected:
            with self.subTest(value=value), self.assertRaises(NarrationError):
                validate_identifier(value, "id")


if __name__ == "__main__":
    unittest.main()
