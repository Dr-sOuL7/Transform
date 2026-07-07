#!/usr/bin/env bash
# ============================================================
#  Build the single-file executable on Linux/macOS.
#  Self-contained: creates a venv, installs deps, builds.
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/.."

echo "Building Offline Text Transformation..."

if [ ! -x ".venv/bin/python" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi
PY=".venv/bin/python"

echo "Installing dependencies..."
"$PY" -m pip install --quiet --upgrade pip
"$PY" -m pip install --quiet -r requirements.txt

echo "Building executable..."
"$PY" -m PyInstaller --clean --noconfirm packaging/transform.spec

echo
echo "Done! Your app is: dist/TextTransform"
echo "Run it, then use the browser window it opens. Ctrl+C to stop."
