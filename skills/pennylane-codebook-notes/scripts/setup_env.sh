#!/usr/bin/env bash
# Ensures a python venv with curl_cffi exists, and checks for the system
# tools this skill's scripts shell out to. Safe to re-run (idempotent).
#
# Usage: source scripts/setup_env.sh <workdir>
# After sourcing, the venv is activated in the current shell.
set -e

WORKDIR="${1:?usage: source setup_env.sh <workdir>}"
VENV="$WORKDIR/venv"

if [ ! -d "$VENV" ]; then
  echo "[setup_env] creating venv at $VENV"
  python3 -m venv "$VENV"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"

python3 -c "import curl_cffi" 2>/dev/null || {
  echo "[setup_env] installing curl_cffi"
  pip install -q -U "curl_cffi>=0.15.0"
}

missing=()
for tool in pdflatex pdfcrop pdftoppm rsvg-convert; do
  command -v "$tool" >/dev/null 2>&1 || missing+=("$tool")
done
if [ ${#missing[@]} -gt 0 ]; then
  echo "[setup_env] WARNING: missing system tools: ${missing[*]}"
  echo "  pdflatex/pdfcrop/pdftoppm come from a TeX Live / MacTeX install."
  echo "  rsvg-convert: brew install librsvg"
fi
echo "[setup_env] ready."
