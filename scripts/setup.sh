#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYTHON_BIN="${BEREIA_AUDIO_PYTHON:-/opt/homebrew/bin/python3.12}"

cd "${PROJECT_ROOT}"

if [[ "$(uname -s)" != "Darwin" || "$(uname -m)" != "arm64" ]]; then
  echo "setup requires macOS arm64" >&2
  exit 3
fi
if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Python 3.12 not found at ${PYTHON_BIN}" >&2
  exit 3
fi
if [[ -x .venv/bin/python ]] && ! .venv/bin/python -c \
  'import sys; raise SystemExit(sys.version_info[:2] != (3, 12))'; then
  echo "existing .venv is not Python 3.12; move it aside before setup" >&2
  exit 3
fi
for executable in ffmpeg ffprobe codex; do
  if ! command -v "${executable}" >/dev/null 2>&1; then
    echo "required executable is unavailable: ${executable}" >&2
    exit 3
  fi
done

"${PYTHON_BIN}" -m venv .venv
export PIP_DISABLE_PIP_VERSION_CHECK=1
export HF_HUB_DISABLE_TELEMETRY=1
.venv/bin/python -m pip install --require-hashes -r requirements.lock
.venv/bin/python -m pip install --no-deps --no-build-isolation -e .
.venv/bin/bereia-audio inspect
.venv/bin/python -m bereia_audio.setup_smoke
