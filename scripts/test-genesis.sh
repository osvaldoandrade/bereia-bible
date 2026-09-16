#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CLI="${PROJECT_ROOT}/.venv/bin/bereia-audio"

cd "${PROJECT_ROOT}"
if [[ ! -x "${CLI}" ]]; then
  echo "run ./scripts/setup.sh first" >&2
  exit 3
fi

"${CLI}" analyze --book GEN --chapter 1
"${CLI}" generate --book GEN --chapter 1

for artifact in narration.json metadata.json chapter.wav chapter.m4a; do
  test -s "output/GEN/001/${artifact}"
done

.venv/bin/python - <<'PY'
from pathlib import Path

from bereia_audio.bible import BibleRepository
from bereia_audio.narration import load_narration_artifact
from bereia_audio.registry import load_registry

root = Path.cwd()
chapter = BibleRepository(root).get_chapter("GEN", 1)
registry = load_registry(root / "character_registry.json")
load_narration_artifact(root / "output/GEN/001/narration.json", chapter, registry)
PY

ffprobe -v error -select_streams a:0 \
  -show_entries stream=codec_name,sample_rate,channels:format=duration \
  -of json output/GEN/001/chapter.wav
ffprobe -v error -select_streams a:0 \
  -show_entries stream=codec_name,sample_rate,channels:format=duration \
  -of json output/GEN/001/chapter.m4a
