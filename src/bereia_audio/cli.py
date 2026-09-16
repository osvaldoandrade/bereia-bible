"""Public command-line contract for Bereia audio production."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .bible import find_repository_root
from .errors import BereiaAudioError
from .pipeline import AudioPipeline
from .telemetry import emit


def build_parser() -> argparse.ArgumentParser:
    """build_parser declares the stable public CLI surface."""

    parser = argparse.ArgumentParser(
        prog="bereia-audio",
        description="Local Bible audiobook production for Apple M4 Max / MLX",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("inspect", help="validate repository, hardware, MLX, and FFmpeg")

    analyze = commands.add_parser("analyze", help="create reviewable narration metadata")
    _add_chapter_coordinate(analyze)

    generate = commands.add_parser("generate", help="generate and master one chapter")
    _add_chapter_coordinate(generate)
    generate.add_argument("--voice", type=Path, help="narrator reference WAV")

    generate_book = commands.add_parser(
        "generate-book", help="generate every discovered chapter sequentially"
    )
    generate_book.add_argument("--book", required=True, help="book identifier, e.g. GEN")
    return parser


def main(argv: list[str] | None = None) -> int:
    """main dispatches commands and maps typed failures to stable exit codes."""

    args = build_parser().parse_args(argv)
    try:
        root = find_repository_root()
        pipeline = AudioPipeline(root)
        if args.command == "inspect":
            result: object = pipeline.inspect()
        elif args.command == "analyze":
            result = pipeline.analyze(args.book, args.chapter)
        elif args.command == "generate":
            result = pipeline.generate(args.book, args.chapter, narrator_voice=args.voice)
        elif args.command == "generate-book":
            result = pipeline.generate_book(args.book)
        else:  # pragma: no cover - argparse makes this unreachable
            raise AssertionError(f"unhandled command: {args.command}")
    except BereiaAudioError as exc:
        emit("command.failed", command=args.command, error_type=type(exc).__name__)
        sys.stderr.write(f"bereia-audio: {exc}\n")
        return exc.exit_code
    except KeyboardInterrupt:
        emit("command.interrupted", command=args.command)
        return 130
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


def _add_chapter_coordinate(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--book", required=True, help="book identifier, e.g. GEN")
    parser.add_argument("--chapter", required=True, type=_positive_integer)


def _positive_integer(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("chapter must be a positive integer") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("chapter must be a positive integer")
    return parsed
