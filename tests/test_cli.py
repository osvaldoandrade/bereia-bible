"""Stable CLI syntax and typed failure behavior."""

from __future__ import annotations

import io
import json
import unittest
from unittest.mock import MagicMock, patch

from bereia_audio.cli import build_parser, main
from bereia_audio.errors import SourceError


class CLITests(unittest.TestCase):
    def test_required_commands_parse(self) -> None:
        parser = build_parser()
        cases = [
            ["inspect"],
            ["analyze", "--book", "GEN", "--chapter", "1"],
            ["generate", "--book", "GEN", "--chapter", "1"],
            ["generate", "--book", "GEN", "--chapter", "1", "--voice", "voices/narrator.wav"],
            ["generate-book", "--book", "GEN"],
        ]

        self.assertEqual(
            [parser.parse_args(case).command for case in cases],
            [
                "inspect",
                "analyze",
                "generate",
                "generate",
                "generate-book",
            ],
        )

    def test_source_failure_maps_to_exit_code_four(self) -> None:
        pipeline = MagicMock()
        pipeline.analyze.side_effect = SourceError("invalid source")
        stderr = io.StringIO()
        with (
            patch("bereia_audio.cli.find_repository_root", return_value="/tmp/repo"),
            patch("bereia_audio.cli.AudioPipeline", return_value=pipeline),
            patch("sys.stderr", stderr),
        ):
            code = main(["analyze", "--book", "GEN", "--chapter", "1"])

        self.assertEqual(code, 4)
        self.assertIn("invalid source", stderr.getvalue())

    def test_success_is_json_on_stdout(self) -> None:
        pipeline = MagicMock()
        pipeline.inspect.return_value = {"supported": True}
        stdout = io.StringIO()
        with (
            patch("bereia_audio.cli.find_repository_root", return_value="/tmp/repo"),
            patch("bereia_audio.cli.AudioPipeline", return_value=pipeline),
            patch("sys.stdout", stdout),
        ):
            code = main(["inspect"])

        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout.getvalue()), {"supported": True})


if __name__ == "__main__":
    unittest.main()
