"""Narration-director trust boundary and artifact contracts."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from bereia_audio import bible
from bereia_audio.errors import NarrationError
from bereia_audio.integrity import build_source_units
from bereia_audio.narration import analyze_chapter, load_narration_artifact
from bereia_audio.narration_contract import validate_director_result
from bereia_audio.registry import load_registry
from tests.support import ContextDirector, director_segment


class NarrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.chapter = bible.get_chapter("GEN", 1)
        cls.units = build_source_units(cls.chapter)

    def test_analysis_identifies_god_for_direct_speech(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_registry(root)
            output = root / "narration.json"

            artifact, _ = analyze_chapter(self.chapter, root, output, runner=ContextDirector())

            quoted = [segment for segment in artifact["segments"] if segment["character"]]
            self.assertTrue(quoted)
            self.assertEqual({segment["speaker"] for segment in quoted}, {"god"})
            self.assertEqual({segment["voice_id"] for segment in quoted}, {"god"})

    def test_artifact_contains_explicit_narration_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_registry(root)
            artifact, _ = analyze_chapter(
                self.chapter, root, root / "narration.json", runner=ContextDirector()
            )
            required = {
                "speaker",
                "character",
                "voice_id",
                "tone",
                "pace",
                "pause_before_ms",
                "pause_after_ms",
                "prosody",
            }

            self.assertTrue(all(required <= set(segment) for segment in artifact["segments"]))

    def test_hydrated_text_is_exclusively_source_units(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_registry(root)
            artifact, _ = analyze_chapter(
                self.chapter, root, root / "narration.json", runner=ContextDirector()
            )

            self.assertEqual(
                "".join(segment["text"] for segment in artifact["segments"]),
                self.chapter.source_text,
            )

    def test_saved_text_mutation_fails_before_generation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_registry(root)
            output = root / "narration.json"
            artifact, _ = analyze_chapter(self.chapter, root, output, runner=ContextDirector())
            artifact["segments"][0]["text"] += " changed"
            output.write_text(json.dumps(artifact), encoding="utf-8")

            with self.assertRaisesRegex(NarrationError, "changed source text"):
                load_narration_artifact(
                    output, self.chapter, load_registry(root / "character_registry.json")
                )

    def test_saved_voice_remap_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_registry(root)
            output = root / "narration.json"
            artifact, _ = analyze_chapter(self.chapter, root, output, runner=ContextDirector())
            direct = next(segment for segment in artifact["segments"] if segment["character"])
            direct["voice_id"] = "different"
            output.write_text(json.dumps(artifact), encoding="utf-8")

            with self.assertRaisesRegex(NarrationError, "character registry"):
                load_narration_artifact(
                    output, self.chapter, load_registry(root / "character_registry.json")
                )

    def test_director_cannot_return_text(self) -> None:
        segments = [director_segment(unit) for unit in self.units]
        segments[0]["text"] = "attempted rewrite"
        raw = {"literary_type": "narrative", "segments": segments}

        with self.assertRaisesRegex(NarrationError, "unknown or missing"):
            validate_director_result(raw, self.units)

    def test_director_must_identify_quoted_character(self) -> None:
        segments = [director_segment(unit) for unit in self.units]
        quoted = next(index for index, unit in enumerate(self.units) if unit.quoted)
        segments[quoted] = director_segment(
            self.units[quoted], speaker="narrator", character=None, voice_id="narrator"
        )

        with self.assertRaisesRegex(NarrationError, "identified character"):
            validate_director_result(
                {"literary_type": "narrative", "segments": segments}, self.units
            )

    def test_director_must_cover_units_once_in_order(self) -> None:
        segments = [director_segment(unit) for unit in self.units]
        segments[1]["unit_ids"] = copy.copy(segments[0]["unit_ids"])

        with self.assertRaisesRegex(NarrationError, "exactly once"):
            validate_director_result(
                {"literary_type": "narrative", "segments": segments}, self.units
            )

    def test_control_boundaries_are_enforced(self) -> None:
        cases = [
            ("pace", 0.74),
            ("pace", 1.16),
            ("pause_after_ms", -1),
            ("pause_after_ms", 3001),
            ("temperature", 1.21),
            ("prosody", {"pitch": "extreme", "energy": 0.5, "cadence": "measured"}),
        ]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                segments = [director_segment(unit) for unit in self.units]
                segments[0][field] = value
                with self.assertRaises(NarrationError):
                    validate_director_result(
                        {"literary_type": "narrative", "segments": segments}, self.units
                    )

    @staticmethod
    def _write_registry(root: Path) -> None:
        (root / "character_registry.json").write_text(
            json.dumps(
                {
                    "narrator": {
                        "voice_id": "narrator",
                        "description": "neutral biblical narrator",
                    },
                    "god": {"voice_id": "god", "description": "controlled and deliberate"},
                }
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
