#!/usr/bin/env python3
"""
Replace every `src="__IMG__/<filename>"` reference in an HTML file with a
base64 data: URI, sourcing files from <output_dir>/formulas/ and
<output_dir>/diagrams/. Produces a single self-contained HTML file, which
is what the Artifact tool requires and what makes copy/paste into Google
Docs carry the images along.

Usage:
    python3 embed_images.py <src.html> <output_dir> <final.html>
"""
import re
import os
import sys
import base64

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("usage: python3 embed_images.py <src.html> <output_dir> <final.html>", file=sys.stderr)
        sys.exit(1)
    src_path, out_dir, final_path = sys.argv[1:4]
    src = open(src_path, encoding="utf-8").read()
    search_dirs = [os.path.join(out_dir, "formulas"), os.path.join(out_dir, "diagrams")]
    missing = []

    def repl(m):
        fname = m.group(1)
        for d in search_dirs:
            path = os.path.join(d, fname)
            if os.path.exists(path):
                data = base64.b64encode(open(path, "rb").read()).decode()
                return f'src="data:image/png;base64,{data}"'
        missing.append(fname)
        return m.group(0)

    out = re.sub(r'src="__IMG__/([^"]+)"', repl, src)
    if missing:
        print("MISSING (left as-is):", missing, file=sys.stderr)
    open(final_path, "w", encoding="utf-8").write(out)
    print("wrote", final_path, "size=", len(out), "missing=", len(missing))
