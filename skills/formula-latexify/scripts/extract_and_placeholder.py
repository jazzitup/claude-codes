#!/usr/bin/env python3
"""
Step 1 of formula-latexify: pull every formula-image out of a lecture note
(HTML or Markdown) and swap it for a plain-text placeholder, so a later
pass can drop in real $$...$$ LaTeX without touching anything else.

Input formats:
  --input foo.html   A self-contained HTML note (e.g. pennylane-codebook-notes
                      output). The whole document is converted to Markdown
                      (via `markdownify`) AFTER every base64 <img> -- formula
                      or not -- is replaced with a plain-text placeholder, so
                      no other tag (headings, lists, bold/italic, tables)
                      touches an <img> during the markdownify pass. This
                      matters: markdownify's table-cell handling silently
                      DROPS <img> tags placed directly inside <td> (no error,
                      no placeholder, the image just vanishes) -- discovered
                      the hard way on notes with gate-matrix images sitting
                      bare inside HTML summary tables. Placeholdering every
                      image first, and only restoring/rendering them after
                      markdownify has already run, sidesteps that bug
                      entirely regardless of where an image sits in the DOM.
  --input foo.md      A Markdown note that already has
                      `<div class="formula">...![](data:image/png;base64,...)...</div>`
                      blocks (raw HTML passthrough inside blank-line-separated
                      markdown). No markdownify pass is needed -- this mode
                      just does the same image-extraction + placeholder swap
                      directly on the markdown text. (Table-drop bug does not
                      apply here since there's no markdownify pass.)

Every base64 image is classified as it's found:
  - "formula"  -- has an ancestor element whose class list includes
                  "formula". Needs a human (Claude) to look at the PNG and
                  transcribe it to LaTeX.
  - "diagram"  -- everything else NOT inside a <table>. Assumed to be a
                  real diagram/portrait, not a formula. Restored to a plain
                  markdown image automatically by THIS script -- no manifest
                  entry, no placeholder left behind, nothing for Claude to
                  do.
  - "review"   -- inside a <table> (e.g. <td>) but NOT class="formula".
                  Ambiguous by construction: lecture notes in this pipeline
                  have used bare, unwrapped <img> formula renders inside
                  "gate summary table" cells before, which look exactly like
                  a genuine diagram at the HTML level. Left as a placeholder
                  for Claude to look at and decide, one by one, whether it's
                  really a formula (transcribe to LaTeX) or a genuine image
                  (put it back as-is).

Placeholders look like ZQFORMULAZQ007ZQ (uppercase letters + digits only).
This matters: markdownify (and most markdown escapers) backslash-escape
`_`, `*`, `[`, etc. inside plain text, which would corrupt LaTeX if we
substituted it in before the HTML->MD pass. An alnum-only token survives
untouched, so the real LaTeX/image is substituted in a later, separate pass
(apply_latex.py) that works directly on the final markdown text.

Produces:
  <workdir>/formulas/<NNN>.png|jpg   one file per "formula"/"review" image
                                      (i.e. everything Claude needs to look
                                      at), in document order. "diagram"
                                      images are NOT saved here -- they're
                                      already back in intermediate.md.
  <workdir>/intermediate.md          the note with diagrams restored and
                                      formula/review placeholders in place
  <workdir>/manifest.json            [{"index": 1, "file": "001.png",
                                       "placeholder": "ZQFORMULAZQ001ZQ",
                                       "kind": "formula"}, ...]
                                      -- only formula/review entries, in the
                                      SAME order Claude must supply LATEX[]
                                      entries in for apply_latex.py.

Usage:
    python3 extract_and_placeholder.py --input <foo.html|foo.md> --workdir <dir>
"""
import argparse
import base64
import json
import os
import re
import sys

PLACEHOLDER_TMPL = "ZQFORMULAZQ{:03d}ZQ"
MIME_EXT = {"png": "png", "jpeg": "jpg", "jpg": "jpg"}


def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def process_html(html_text: str, formulas_dir: str):
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        die("Missing dependency: beautifulsoup4. Install with `pip3 install beautifulsoup4 markdownify`.")
    try:
        import markdownify
    except ImportError:
        die("Missing dependency: markdownify. Install with `pip3 install beautifulsoup4 markdownify`.")

    soup = BeautifulSoup(html_text, "html.parser")
    manifest = []
    idx = 0
    for img in soup.find_all("img"):
        src = img.get("src", "")
        m = re.match(r"data:image/(png|jpe?g);base64,([A-Za-z0-9+/=]+)", src or "")
        if not m:
            continue
        idx += 1
        mime, b64 = m.group(1), m.group(2)
        ext = MIME_EXT.get(mime, "png")
        data = base64.b64decode(b64)
        placeholder = PLACEHOLDER_TMPL.format(idx)

        is_formula = img.find_parent(class_="formula") is not None
        is_in_table = img.find_parent("table") is not None
        kind = "formula" if is_formula else ("review" if is_in_table else "diagram")

        if kind == "diagram":
            # Not a formula, not ambiguous -- keep it a real image, restore
            # immediately after conversion via its own dedicated placeholder
            # so markdownify never touches a data-uri <img> (table-drop bug).
            img["src"] = f"__DIAGRAM_{idx}__"
        else:
            fname = f"{idx:03d}.{ext}"
            with open(os.path.join(formulas_dir, fname), "wb") as f:
                f.write(data)
            manifest.append({"index": idx, "file": fname, "placeholder": placeholder, "kind": kind})
            img.replace_with(soup.new_string(placeholder))
            continue

        # kind == "diagram": leave the (now placeholder-src) <img> tag itself
        # in place so markdownify still emits a normal ![]() for it; we
        # substitute the real data: URI back in afterwards (see below).
        img["_diagram_b64"] = f"data:image/{mime};base64,{b64}"

    body = soup.body if soup.body else soup
    # Collect diagram restorations before stringifying (attribute values
    # survive str(body) fine, but easier to build a lookup up front).
    diagram_restores = {}
    for img in soup.find_all("img"):
        src = img.get("src", "")
        dm = re.match(r"__DIAGRAM_(\d+)__$", src)
        if dm:
            diagram_restores[src] = img.get("_diagram_b64")
            del img["_diagram_b64"]

    md_text = markdownify.markdownify(str(body), heading_style="ATX", bullets="-")
    for placeholder_src, real_uri in diagram_restores.items():
        md_text = md_text.replace(f"({placeholder_src})", f"({real_uri})")

    return md_text, manifest


def process_markdown(md_text: str, formulas_dir: str):
    img_pattern = re.compile(r'!\[\]\(data:image/(png|jpe?g);base64,([A-Za-z0-9+/=]+)\)')
    formula_div_pattern = re.compile(r'<div class="formula">(.*?)</div>', re.S)

    formula_spans = [(m.start(1), m.end(1)) for m in formula_div_pattern.finditer(md_text)]

    def in_formula_span(pos):
        return any(a <= pos < b for a, b in formula_spans)

    manifest = []
    idx_holder = {"i": 0}

    def repl(m):
        idx_holder["i"] += 1
        idx = idx_holder["i"]
        if not in_formula_span(m.start()):
            return m.group(0)  # non-formula images in a plain .md are left as-is
        mime, b64 = m.group(1), m.group(2)
        ext = MIME_EXT.get(mime, "png")
        data = base64.b64decode(b64)
        fname = f"{idx:03d}.{ext}"
        with open(os.path.join(formulas_dir, fname), "wb") as f:
            f.write(data)
        placeholder = PLACEHOLDER_TMPL.format(idx)
        manifest.append({"index": idx, "file": fname, "placeholder": placeholder, "kind": "formula"})
        return placeholder

    new_text = img_pattern.sub(repl, md_text)
    return new_text, manifest


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Source .html or .md file")
    ap.add_argument("--workdir", required=True, help="Output directory (created if missing)")
    args = ap.parse_args()

    os.makedirs(args.workdir, exist_ok=True)
    formulas_dir = os.path.join(args.workdir, "formulas")
    os.makedirs(formulas_dir, exist_ok=True)

    src_text = open(args.input, encoding="utf-8").read()
    ext = os.path.splitext(args.input)[1].lower()

    if ext in (".html", ".htm"):
        md_text, manifest = process_html(src_text, formulas_dir)
    elif ext == ".md":
        md_text, manifest = process_markdown(src_text, formulas_dir)
    else:
        die(f"Unsupported extension: {ext} (expected .html or .md)")

    inter_path = os.path.join(args.workdir, "intermediate.md")
    with open(inter_path, "w", encoding="utf-8") as f:
        f.write(md_text)

    manifest_path = os.path.join(args.workdir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)

    n_formula = sum(1 for e in manifest if e["kind"] == "formula")
    n_review = sum(1 for e in manifest if e["kind"] == "review")
    print(f"formula images: {n_formula}")
    if n_review:
        print(f"review images (in a table, not class=formula -- inspect each one): {n_review}")
    print(f"wrote {inter_path}")
    print(f"wrote {manifest_path}")
    print(f"wrote {len(manifest)} image files to {formulas_dir}/")
