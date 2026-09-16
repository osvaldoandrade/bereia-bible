"""Published JSON artifacts remain parseable and versioned."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


class SchemaTests(unittest.TestCase):
    def test_audio_schemas_are_valid_json_objects(self) -> None:
        paths = [
            Path("api/narration-director.schema.json"),
            Path("api/narration-artifact.schema.json"),
            Path("api/audio-metadata.schema.json"),
            Path("api/character-registry.schema.json"),
        ]
        for path in paths:
            with self.subTest(path=path):
                schema = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
                self.assertEqual(schema["type"], "object")

    def test_character_registry_matches_public_shape(self) -> None:
        registry = json.loads(Path("character_registry.json").read_text(encoding="utf-8"))

        self.assertIn("narrator", registry)
        self.assertEqual(registry["god"]["voice_id"], "god")


if __name__ == "__main__":
    unittest.main()
