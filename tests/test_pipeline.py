"""End-to-end orchestration with a non-Chatterbox synthesizer fake."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bereia_audio.bible import BibleRepository
from bereia_audio.narration import analyze_chapter
from bereia_audio.pipeline import AudioPipeline, chapter_paths
from tests.support import ContextDirector, FakeSynthesizer, make_repository

_RUNTIME_REPORT = {
    "supported": True,
    "hardware": {
        "system": "Darwin",
        "architecture": "arm64",
        "model": "MacBook Pro",
        "chip": "Apple M4 Max",
        "memory_gb": 128,
    },
    "runtime": "mps",
    "framework": "mlx",
    "accelerator": "metal",
    "tools": {"ffmpeg": "/opt/homebrew/bin/ffmpeg", "ffprobe": "/opt/homebrew/bin/ffprobe"},
}


class PipelineTests(unittest.TestCase):
    def test_generate_publishes_metadata_audio_and_reuses_chapter_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = make_repository(Path(temporary))
            chapter = BibleRepository(root).get_chapter("GEN", 1)
            paths = chapter_paths(root, "GEN", 1)
            analyze_chapter(
                chapter,
                root,
                paths["narration"],
                runner=ContextDirector(),
            )
            synthesizer = FakeSynthesizer()
            pipeline = AudioPipeline(root, synthesizer=synthesizer)

            with patch("bereia_audio.pipeline.inspect_environment", return_value=_RUNTIME_REPORT):
                first = pipeline.generate("GEN", 1)
                mtimes = (paths["wav"].stat().st_mtime_ns, paths["m4a"].stat().st_mtime_ns)
                second = pipeline.generate("GEN", 1)

            metadata = json.loads(paths["metadata"].read_text(encoding="utf-8"))
            self.assertFalse(first["cache_hit"])
            self.assertTrue(second["cache_hit"])
            self.assertEqual(
                (paths["wav"].stat().st_mtime_ns, paths["m4a"].stat().st_mtime_ns), mtimes
            )
            self.assertEqual(len(synthesizer.calls), len(metadata["segments"]))
            self.assertEqual(metadata["runtime"], "mps")
            self.assertEqual(metadata["framework"], "mlx")
            self.assertEqual(metadata["hardware"], "Apple M4 Max")
            self.assertEqual(metadata["seed"], 1234)
            self.assertRegex(metadata["source_commit"], r"^[0-9a-f]{40}$")
            self.assertTrue(paths["wav"].is_file())
            self.assertTrue(paths["m4a"].is_file())

    def test_partial_segment_cache_resumes_without_reusing_changed_segment(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = make_repository(Path(temporary))
            chapter = BibleRepository(root).get_chapter("GEN", 1)
            paths = chapter_paths(root, "GEN", 1)
            artifact, _ = analyze_chapter(
                chapter,
                root,
                paths["narration"],
                runner=ContextDirector(),
            )
            synthesizer = FakeSynthesizer()
            pipeline = AudioPipeline(root, synthesizer=synthesizer)
            with patch("bereia_audio.pipeline.inspect_environment", return_value=_RUNTIME_REPORT):
                pipeline.generate("GEN", 1)
                paths["wav"].unlink()
                paths["m4a"].unlink()
                segment_path = paths["segments"] / f"{artifact['segments'][0]['segment_id']}.wav"
                segment_path.write_bytes(b"corrupted")
                pipeline.generate("GEN", 1)

            first_segment_calls = [call for call in synthesizer.calls if call[0] == "s0001"]
            other_segment_calls = [call for call in synthesizer.calls if call[0] != "s0001"]
            self.assertEqual(len(first_segment_calls), 2)
            self.assertEqual(len(other_segment_calls), len(artifact["segments"]) - 1)


if __name__ == "__main__":
    unittest.main()
