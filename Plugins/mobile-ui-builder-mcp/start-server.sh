#!/bin/bash
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"

# Check Python 3.13+ is available
if ! command -v python3 &>/dev/null; then
  echo "[mobile-ui-builder] ERROR: python3 not found." >&2
  echo "[mobile-ui-builder] Install Python 3.13+ from https://www.python.org/downloads/ or via Homebrew: brew install python@3.13" >&2
  exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 13 ]; }; then
  echo "[mobile-ui-builder] ERROR: Python 3.13+ is required (found $PYTHON_VERSION)." >&2
  echo "[mobile-ui-builder] Install via Homebrew: brew install python@3.13" >&2
  exit 1
fi

if [ ! -d "$DIR/.venv" ]; then
  echo "[mobile-ui-builder] Creating virtual environment..." >&2
  python3 -m venv "$DIR/.venv"
  "$DIR/.venv/bin/pip" install --quiet -r "$DIR/requirements.txt"
  echo "[mobile-ui-builder] Setup complete." >&2
fi
exec "$DIR/.venv/bin/python" "$DIR/server/server.py"
