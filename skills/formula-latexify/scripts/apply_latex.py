#!/usr/bin/env python3
"""
Step 3 of formula-latexify: substitute each ZQFORMULAZQ<NNN>ZQ placeholder
left by extract_and_placeholder.py with either the real $$...$$ LaTeX block
Claude transcribed by looking at <workdir>/formulas/<NNN>.png|jpg, or -- for
a "review"-kind entry that turned out to be a genuine image, not a formula
-- the original image, restored as a normal markdown ![]().

Between step 1 and this step, Claude must:
  - Read every file in <workdir>/formulas/ (in order)
  - Write <workdir>/latex_bodies.py containing a top-level list called
    LATEX, one entry per manifest.json entry, in the SAME order
    (LATEX[0] corresponds to manifest[0], etc.). Each entry is either:
      - a raw triple-quoted LaTeX string (r\"\"\"...\"\"\"), for a real formula
        (do NOT include the surrounding $$ markers -- this script adds them)
      - the literal string "__IMAGE__", for a "review"-kind entry that
        turned out to be a genuine diagram/photo, not a formula -- this
        script puts the original image back in its place instead.

Usage:
    python3 apply_latex.py --intermediate <workdir>/intermediate.md \
        --latex <workdir>/latex_bodies.py --manifest <workdir>/manifest.json \
        --workdir <workdir> --output <final.md>
"""
import argparse
import base64
import importlib.util
import json
import os
import sys

MIME_BY_EXT = {"png": "png", "jpg": "jpeg", "jpeg": "jpeg"}


def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def load_latex_list(path):
    spec = importlib.util.spec_from_file_location("latex_bodies", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "LATEX"):
        die(f"{path} does not define a top-level LATEX list")
    return mod.LATEX


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--intermediate", required=True)
    ap.add_argument("--latex", required=True, help="Python file defining LATEX = [...]")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--workdir", required=True, help="Dir containing formulas/ (needed to restore __IMAGE__ entries)")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    text = open(args.intermediate, encoding="utf-8").read()
    manifest = json.load(open(args.manifest, encoding="utf-8"))
    latex_list = load_latex_list(args.latex)

    if len(latex_list) != len(manifest):
        die(f"LATEX has {len(latex_list)} entries but manifest has {len(manifest)} formulas -- "
            f"these must match 1:1 in order.")

    missing = []
    for entry, latex in zip(manifest, latex_list):
        placeholder = entry["placeholder"]
        if placeholder not in text:
            missing.append(placeholder)
            continue
        if latex.strip() == "__IMAGE__":
            img_path = os.path.join(args.workdir, "formulas", entry["file"])
            ext = os.path.splitext(entry["file"])[1].lstrip(".").lower()
            mime = MIME_BY_EXT.get(ext, "png")
            b64 = base64.b64encode(open(img_path, "rb").read()).decode()
            block = f"![](data:image/{mime};base64,{b64})"
        else:
            block = f"$$\n{latex.strip()}\n$$"
        text = text.replace(placeholder, block, 1)

    if missing:
        die(f"placeholders not found in intermediate.md (already consumed twice, or manifest/file mismatch): {missing}")

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(text)

    n_latex = sum(1 for l in latex_list if l.strip() != "__IMAGE__")
    n_image = len(latex_list) - n_latex
    print(f"substituted {n_latex} formula(s) as LaTeX, {n_image} restored as image(s)")
    print(f"wrote {args.output}")
