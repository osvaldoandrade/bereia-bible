"""Persistent character-registry stability contracts."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bereia_audio.errors import NarrationError
from bereia_audio.registry import (
    ensure_characters,
    load_registry,
    registry_bindings,
    registry_sha256,
    write_registry,
)


class RegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = {
            "narrator": {"voice_id": "narrator", "description": "neutral"},
            "god": {"voice_id": "god", "description": "deliberate"},
        }

    def test_existing_character_voice_never_remaps(self) -> None:
        segments = [
            {
                "character": "god",
                "voice_id": "random-occurrence",
                "character_description": "attempted remap",
            }
        ]

        updated, changed = ensure_characters(self.registry, segments)

        self.assertFalse(changed)
        self.assertEqual(updated["god"]["voice_id"], "god")

    def test_new_character_gets_stable_canonical_voice(self) -> None:
        segments = [
            {
                "character": "angel",
                "voice_id": "ignored-choice",
                "character_description": "calm messenger",
            }
        ]

        updated, changed = ensure_characters(self.registry, segments)

        self.assertTrue(changed)
        self.assertEqual(updated["angel"], {"voice_id": "angel", "description": "calm messenger"})

    def test_new_character_requires_description(self) -> None:
        with self.assertRaisesRegex(NarrationError, "requires a description"):
            ensure_characters(
                self.registry,
                [{"character": "angel", "voice_id": "angel", "character_description": None}],
            )

    def test_atomic_round_trip_is_sorted_and_stable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "registry.json"
            write_registry(path, self.registry)
            first_hash = registry_sha256(load_registry(path))
            write_registry(path, load_registry(path))

            self.assertEqual(registry_sha256(load_registry(path)), first_hash)
            self.assertEqual(list(json.loads(path.read_text())), ["god", "narrator"])

    def test_bindings_are_limited_to_used_characters_and_narrator(self) -> None:
        self.assertEqual(
            registry_bindings(self.registry, {"god"}),
            {"god": "god", "narrator": "narrator"},
        )

    def test_invalid_registry_profile_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "registry.json"
            path.write_text('{"narrator":{"voice_id":"Narrator"}}', encoding="utf-8")

            with self.assertRaises(NarrationError):
                load_registry(path)


if __name__ == "__main__":
    unittest.main()
