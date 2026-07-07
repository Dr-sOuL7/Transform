#!/usr/bin/env bash
# Build the single-file executable on Linux/macOS.
set -euo pipefail
cd "$(dirname "$0")/.."

python -m pip install --quiet --upgrade pyinstaller
python -m PyInstaller --clean --noconfirm packaging/transform.spec

echo
echo "Built: dist/TextTransform"
echo "Run it, then open the browser window it launches."
