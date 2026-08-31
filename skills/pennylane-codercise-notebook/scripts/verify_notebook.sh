#!/usr/bin/env bash
# Build a throwaway venv with the same PennyLane version Colab currently
# installs, then execute a notebook end-to-end and fail loudly on error.
#
# Usage: verify_notebook.sh <workdir> <notebook.ipynb>
set -euo pipefail

WORKDIR="$1"
NB="$2"

if [ ! -d "$WORKDIR/venv" ]; then
  echo "[verify_notebook] creating venv at $WORKDIR/venv"
  python3 -m venv "$WORKDIR/venv"
  # shellcheck disable=SC1091
  source "$WORKDIR/venv/bin/activate"
  pip install -q --upgrade pip
  pip install -q pennylane matplotlib nbconvert ipykernel
else
  # shellcheck disable=SC1091
  source "$WORKDIR/venv/bin/activate"
fi

python3 -c "import pennylane as qml; print('[verify_notebook] pennylane', qml.__version__)"

OUT="${NB%.ipynb}.executed.ipynb"
jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=180 \
  "$NB" --output "$(basename "$OUT")"

python3 - "$OUT" << 'PYEOF'
import json, sys
nb = json.load(open(sys.argv[1]))
n_errors = 0
for i, cell in enumerate(nb["cells"]):
    if cell.get("cell_type") != "code":
        continue
    for out in cell.get("outputs", []):
        if out.get("output_type") == "error":
            n_errors += 1
            print(f"!! cell {i} ERROR: {out.get('ename')}: {out.get('evalue')}")
if n_errors == 0:
    print(f"[verify_notebook] OK — {len(nb['cells'])} cells, no errors")
else:
    print(f"[verify_notebook] FAILED — {n_errors} cell(s) raised errors")
    sys.exit(1)
PYEOF
