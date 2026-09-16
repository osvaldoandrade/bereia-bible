"""FFmpeg pacing, silence, loudness, and codec behavior."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from bereia_audio.mastering import _resolve_chapter_pauses, master_chapter, probe_audio
from tests.support import write_test_wav


class MasteringTests(unittest.TestCase):
    def test_segment_boundaries_use_one_pause_instead_of_stacking_both_sides(
        self,
    ) -> None:
        first = Path("first.wav")
        second = Path("second.wav")
        third = Path("third.wav")
        segments = [
            (
                first,
                {"pace": 1.0, "pause_before_ms": 50, "pause_after_ms": 300},
            ),
            (
                second,
                {"pace": 1.0, "pause_before_ms": 500, "pause_after_ms": 200},
            ),
            (
                third,
                {"pace": 1.0, "pause_before_ms": 100, "pause_after_ms": 400},
            ),
        ]

        resolved = _resolve_chapter_pauses(segments)

        self.assertEqual(
            [(before, after) for _, _, before, after in resolved],
            [(50, 500), (0, 200), (0, 400)],
        )

    def test_mastering_produces_valid_wav_and_m4a_with_pauses(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "s0001.wav"
            second = root / "s0002.wav"
            write_test_wav(first, duration=0.3)
            write_test_wav(second, duration=0.3, frequency=330.0)
            metadata = {
                "pace": 1.0,
                "pause_before_ms": 50,
                "pause_after_ms": 100,
            }

            result = master_chapter(
                [(first, metadata), (second, metadata)],
                root / "chapter.wav",
                root / "chapter.m4a",
                title="GEN 1",
                album="GEN",
                source_commit="0" * 40,
            )

            self.assertGreater(result.duration_seconds, 0.8)
            self.assertLess(result.duration_seconds, 1.0)
            self.assertEqual(
                probe_audio(root / "chapter.wav", expected_codec="pcm_s16le"),
                result.duration_seconds,
            )
            self.assertGreater(probe_audio(root / "chapter.m4a", expected_codec="aac"), 0.0)


if __name__ == "__main__":
    unittest.main()
