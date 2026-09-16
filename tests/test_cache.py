"""Content-addressed cache invalidation contracts."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from bereia_audio.cache import (
    cached_file_matches,
    chapter_fingerprint,
    file_sha256,
    segment_fingerprint,
    tts_identity,
)


class CacheTests(unittest.TestCase):
    def setUp(self) -> None:
        self.narration = {"segments": [{"text": "source", "pace": 1.0}]}
        self.voices = {"narrator": {"reference_sha256": "abc"}}

    def test_same_inputs_produce_same_chapter_key(self) -> None:
        first = chapter_fingerprint("source", self.narration, self.voices, 1234)
        second = chapter_fingerprint("source", self.narration, self.voices, 1234)

        self.assertEqual(first, second)

    def test_each_required_input_invalidates_chapter_key(self) -> None:
        baseline = chapter_fingerprint("source", self.narration, self.voices, 1234)
        cases = [
            chapter_fingerprint("changed", self.narration, self.voices, 1234),
            chapter_fingerprint("source", {"segments": []}, self.voices, 1234),
            chapter_fingerprint(
                "source", self.narration, {"narrator": {"reference_sha256": "def"}}, 1234
            ),
            chapter_fingerprint("source", self.narration, self.voices, 1235),
        ]

        self.assertTrue(all(candidate != baseline for candidate in cases))

    def test_segment_voice_and_seed_invalidate_key(self) -> None:
        segment = {"text": "source", "pace": 1.0}
        voice = {"reference_sha256": "abc"}
        baseline = segment_fingerprint(segment, voice, 10)

        self.assertNotEqual(segment_fingerprint({"text": "other"}, voice, 10), baseline)
        self.assertNotEqual(segment_fingerprint(segment, {"reference_sha256": "def"}, 10), baseline)
        self.assertNotEqual(segment_fingerprint(segment, voice, 11), baseline)

    def test_cached_file_requires_key_and_byte_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "segment.wav"
            path.write_bytes(b"audio")
            cache = {"cache_key": "key", "sha256": file_sha256(path)}

            self.assertTrue(cached_file_matches(path, cache, "key"))
            self.assertFalse(cached_file_matches(path, cache, "other"))
            path.write_bytes(b"mutated")
            self.assertFalse(cached_file_matches(path, cache, "key"))

    def test_tts_identity_is_fully_pinned(self) -> None:
        identity = tts_identity()

        self.assertEqual(identity["package"], "mlx-audio")
        self.assertRegex(str(identity["model_revision"]), r"^[0-9a-f]{40}$")
        self.assertRegex(str(identity["tokenizer_revision"]), r"^[0-9a-f]{40}$")


if __name__ == "__main__":
    unittest.main()
