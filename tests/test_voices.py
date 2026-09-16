"""Voice resolution, validation, and fallback metadata."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from bereia_audio.errors import TTSFailure
from bereia_audio.voices import resolve_voices
from tests.support import write_test_wav


class VoiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.artifact = {"character_bindings": {"god": "god", "narrator": "narrator"}}

    def test_character_specific_reference_wins(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_test_wav(root / "voices/narrator.wav")
            write_test_wav(root / "voices/god.wav", frequency=220.0)

            voices = resolve_voices(self.artifact, root)

            self.assertEqual(voices["god"].reference_label, "voices/god.wav")
            self.assertFalse(voices["god"].fallback)

    def test_missing_character_uses_narrator_and_records_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_test_wav(root / "voices/narrator.wav")

            voices = resolve_voices(self.artifact, root)

            self.assertEqual(voices["god"].resolved_voice_id, "narrator")
            self.assertTrue(voices["god"].fallback)
            self.assertIn("absent", str(voices["god"].fallback_reason))

    def test_no_files_rejects_generation_without_native_narrator(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(TTSFailure, "native Brazilian Portuguese narrator"):
                resolve_voices(self.artifact, Path(temporary))

    def test_cli_override_becomes_narrator_fallback_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            override = root / "custom.wav"
            write_test_wav(override)

            voices = resolve_voices(self.artifact, root, override)

            self.assertEqual(voices["narrator"].reference_path, override.resolve())
            self.assertEqual(voices["god"].reference_path, override.resolve())

    def test_short_reference_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_test_wav(root / "voices/narrator.wav", duration=0.99)

            with self.assertRaisesRegex(TTSFailure, "1-30 seconds"):
                resolve_voices(self.artifact, root)

    def test_non_wav_override_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "voice.mp3"
            path.write_bytes(b"not audio")

            with self.assertRaisesRegex(TTSFailure, "existing WAV"):
                resolve_voices(self.artifact, root, path)


if __name__ == "__main__":
    unittest.main()
