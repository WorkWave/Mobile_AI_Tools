#!/bin/bash
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"

# Returns 0 if the given python binary is 3.13+
python_ok() {
  local bin="$1"
  command -v "$bin" &>/dev/null || return 1
  local maj min
  maj=$("$bin" -c "import sys; print(sys.version_info.major)")
  min=$("$bin" -c "import sys; print(sys.version_info.minor)")
  [ "$maj" -gt 3 ] || { [ "$maj" -eq 3 ] && [ "$min" -ge 13 ]; }
}

# Find a suitable Python 3.13+ binary
PYTHON3=""
for candidate in python3.13 python3.14 python3 "$(brew --prefix python@3.13 2>/dev/null)/bin/python3.13"; do
  if python_ok "$candidate"; then
    PYTHON3="$candidate"
    break
  fi
done

# If not found, try to install via Homebrew
if [ -z "$PYTHON3" ]; then
  if command -v brew &>/dev/null; then
    echo "[mobile-ui-builder] Python 3.13+ not found. Installing via Homebrew..." >&2
    brew install python@3.13 >&2
    BREW_PYTHON="$(brew --prefix python@3.13)/bin/python3.13"
    if python_ok "$BREW_PYTHON"; then
      PYTHON3="$BREW_PYTHON"
    fi
  fi
fi

if [ -z "$PYTHON3" ]; then
  echo "[mobile-ui-builder] ERROR: Python 3.13+ is required and could not be installed automatically." >&2
  echo "[mobile-ui-builder] Install manually: brew install python@3.13" >&2
  echo "[mobile-ui-builder] Or download from: https://www.python.org/downloads/" >&2
  exit 1
fi

if [ ! -d "$DIR/.venv" ]; then
  echo "[mobile-ui-builder] Creating virtual environment..." >&2
  "$PYTHON3" -m venv "$DIR/.venv"
  "$DIR/.venv/bin/pip" install --quiet -r "$DIR/requirements.txt"
  echo "[mobile-ui-builder] Setup complete." >&2
fi
exec "$DIR/.venv/bin/python" "$DIR/server/server.py"
