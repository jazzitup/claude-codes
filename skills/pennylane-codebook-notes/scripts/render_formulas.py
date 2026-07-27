#!/usr/bin/env python3
r"""
Render every $$...$$ display-math block found in one or more extract_theory.py
JSON outputs into a cropped, high-DPI PNG using a real LaTeX install
(pdflatex + pdfcrop + pdftoppm -- all part of a standard TeX Live install).

Rendering is content-addressed (filename = md5 of the LaTeX body), so
formulas that repeat across pages (e.g. the same RY matrix) are only
rendered once, and re-running the script on the same content is a no-op.

Usage:
    python3 render_formulas.py <output_dir> <page1.json> [<page2.json> ...]

Produces:
    <output_dir>/formulas/<hash>.png             (one per unique formula)
    <output_dir>/formula_mapping.json             ({page_slug: [{slug,title,index,latex,png}]})

Notes on the LaTeX quirks this handles (learned the hard way):
  - Source markdown sometimes puts `\tag{n}` *outside* `\end{align*}`/
    `\end{equation}` (valid for MathJax, invalid for real amsmath) --
    stripped automatically.
  - `align*` blocks combined with the `varwidth` standalone class leave a
    large blank margin on one side (a known TeX box-measurement quirk) --
    fixed by cropping the compiled PDF with `pdfcrop` before rasterizing,
    instead of trusting the LaTeX-computed bounding box.
"""
import re
import os
import sys
import json
import hashlib
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEX_TEMPLATE = r"""\documentclass[preview,border=4pt,varwidth]{standalone}
\usepackage{amsmath,amssymb}
\begin{document}
%%BODY%%
\end{document}
"""

ENV_STARTERS = (
    "\\begin{align", "\\begin{equation", "\\begin{gather", "\\begin{alignat",
    "\\begin{eqnarray}", "\\begin{eqnarray*}", "\\begin{multline", "\\begin{flalign",
)


def check_tools():
    missing = [t for t in ("pdflatex", "pdfcrop", "pdftoppm") if subprocess.run(
        ["which", t], capture_output=True).returncode != 0]
    if missing:
        print(f"Missing required tools: {', '.join(missing)}. Install a TeX "
              f"Live / MacTeX distribution (provides pdflatex, pdfcrop, pdftoppm).",
              file=sys.stderr)
        sys.exit(1)


def collect_display_blocks(text: str):
    return re.findall(r"\$\$(.*?)\$\$", text or "", re.S)


def render_formula(body: str, out_dir: str) -> str:
    """Render one LaTeX body to <out_dir>/formulas/<hash>.png; return the
    filename (not path) of the PNG. Skips work if already cached."""
    body = body.strip()
    body = re.sub(r"(\\end\{[a-zA-Z*]+\})[^\\]*\\tag\{[^}]*\}\s*$", r"\1", body)
    key = hashlib.md5(body.encode()).hexdigest()[:16]
    formulas_dir = os.path.join(out_dir, "formulas")
    os.makedirs(formulas_dir, exist_ok=True)
    png_out = os.path.join(formulas_dir, key + ".png")
    if os.path.exists(png_out):
        return key + ".png"

    wrapped = body if any(body.startswith(s) for s in ENV_STARTERS) else "\\[" + body + "\\]"
    tex = TEX_TEMPLATE.replace("%%BODY%%", wrapped)

    build_dir = os.path.join(out_dir, "_build")
    os.makedirs(build_dir, exist_ok=True)
    texfile = os.path.join(build_dir, key + ".tex")
    with open(texfile, "w") as f:
        f.write(tex)

    proc = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", key + ".tex"],
        cwd=build_dir, capture_output=True, text=True,
    )
    pdf = os.path.join(build_dir, key + ".pdf")
    if not os.path.exists(pdf):
        raise RuntimeError(f"pdflatex failed for formula (hash {key}):\n{body}\n---\n{proc.stdout[-2000:]}")

    cropped = os.path.join(build_dir, key + "-crop.pdf")
    subprocess.run(["pdfcrop", "--margins", "6", pdf, cropped], cwd=build_dir, capture_output=True, text=True)
    if not os.path.exists(cropped):
        cropped = pdf

    subprocess.run(
        ["pdftoppm", "-png", "-r", "400", cropped, os.path.join(formulas_dir, key)],
        capture_output=True, text=True,
    )
    candidate = os.path.join(formulas_dir, key + "-1.png")
    if os.path.exists(candidate):
        os.rename(candidate, png_out)
    if not os.path.exists(png_out):
        raise RuntimeError(f"pdftoppm did not produce output for formula (hash {key})")
    return key + ".png"


def process_page(path: str, out_dir: str) -> list:
    data = json.load(open(path, encoding="utf-8"))
    page_slug = os.path.splitext(os.path.basename(path))[0]
    entries = []
    sections = [("theory", t["slug"], t["title"], t["content"]) for t in data.get("theories", [])]
    sections += [("exercise", e["slug"], e.get("title"), e.get("content")) for e in data.get("exercises", []) if e.get("content")]
    for kind, slug, title, text in sections:
        for i, block in enumerate(collect_display_blocks(text)):
            png = render_formula(block, out_dir)
            entries.append({"kind": kind, "slug": slug, "title": title, "index": i, "latex": block.strip(), "png": png})
    return {"page_slug": page_slug, "source_url": data.get("source_url"), "formulas": entries}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: python3 render_formulas.py <output_dir> <page1.json> [<page2.json> ...]", file=sys.stderr)
        sys.exit(1)
    check_tools()
    out_dir, json_paths = sys.argv[1], sys.argv[2:]
    os.makedirs(out_dir, exist_ok=True)
    mapping_path = os.path.join(out_dir, "formula_mapping.json")
    mapping = json.load(open(mapping_path)) if os.path.exists(mapping_path) else {}
    for p in json_paths:
        result = process_page(p, out_dir)
        mapping[result["page_slug"]] = result
        print(result["page_slug"], "formulas:", len(result["formulas"]))
    json.dump(mapping, open(mapping_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("wrote", mapping_path)
