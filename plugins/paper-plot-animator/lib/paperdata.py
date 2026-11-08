"""Get the real numbers of a paper's figure: arXiv source, HEPData, or vector-PDF digitising.

CLI
  python paperdata.py fetch ARXIVID OUTDIR           # arXiv e-print source (figures as PDF) + HEPData yaml if any
  python paperdata.py markers FIG.pdf [--ylog]       # print filled data markers in data coordinates
  python paperdata.py raster FIG.pdf OUT.png [zoom]  # high-res PNG of a vector figure (to show the real plot)

`markers` calibrates the axes from the numeric tick labels found in the PDF text layer (left = y ticks,
bottom = x ticks) and prints the centres of small filled black markers (data points). Legend markers come
out too - drop the ones outside the plotted range. Always cross-check against the figure by eye.
Needs pymupdf (pip install pymupdf).
"""
import os, sys, json, tarfile, io, subprocess, urllib.request
import numpy as np


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "paperdata/1.0"})
    return urllib.request.urlopen(req, timeout=60).read()


def fetch(arxiv, out):
    os.makedirs(out, exist_ok=True)
    blob = _get(f"https://arxiv.org/e-print/{arxiv}")
    src = os.path.join(out, "src"); os.makedirs(src, exist_ok=True)
    try:
        tarfile.open(fileobj=io.BytesIO(blob)).extractall(src, filter="data")
    except tarfile.ReadError:
        open(os.path.join(src, "main.tex.gz"), "wb").write(blob)
    q = json.loads(_get(f"https://inspirehep.net/api/literature?q=arxiv:{arxiv}&fields=control_number"))
    hits = q["hits"]["hits"]
    if hits:
        ins = hits[0]["metadata"]["control_number"]
        try:
            tgz = _get(f"https://www.hepdata.net/download/submission/ins{ins}/1/yaml")
            tarfile.open(fileobj=io.BytesIO(tgz)).extractall(os.path.join(out, "hepdata"), filter="data")
            print("HEPData: ins", ins)
        except Exception as e:
            print("no HEPData for ins", ins, e)
    print("source in", src)


def _ticks(page):
    xs, ys = [], []
    for b in page.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            for s in l["spans"]:
                t = s["text"].strip().replace("−", "-")
                try:
                    v = float(t)
                except ValueError:
                    continue
                x0, y0, x1, y1 = s["bbox"]
                xs.append((v, 0.5 * (x0 + x1), 0.5 * (y0 + y1))); ys.append((v, x1, 0.5 * (y0 + y1)))
    return xs, ys


def markers(pdf, ylog=False):
    import pymupdf
    page = pymupdf.open(pdf)[0]
    xs, ys = _ticks(page)
    # y ticks: right-aligned column with the most labels at the left; x ticks: row with the most labels at the bottom
    xcol = max(set(round(x1) for _, x1, _ in ys), key=lambda c: sum(abs(round(x1) - c) <= 2 for _, x1, _ in ys))
    yt = sorted([(v, yc) for v, x1, yc in ys if abs(round(x1) - xcol) <= 2], key=lambda q: q[1])
    # several panels (e.g. main + ratio) share the column: keep the longest run with values falling downwards
    runs, cur = [], [yt[0]]
    for q in yt[1:]:
        (cur.append(q) if q[0] < cur[-1][0] else (runs.append(cur), cur := [q]))
    runs.append(cur); yt = max(runs, key=len)
    yrow = max(set(round(yc) for _, _, yc in xs), key=lambda c: sum(abs(round(yc) - c) <= 2 for _, _, yc in xs))
    xt = [(v, xc) for v, xc, yc in xs if abs(round(yc) - yrow) <= 2]
    fy = np.polyfit([p for _, p in yt], [np.log10(v) if ylog else v for v, _ in yt], 1)
    fx = np.polyfit([p for _, p in xt], [v for v, _ in xt], 1)
    print("y ticks", [v for v, _ in yt], " x ticks", [v for v, _ in xt])
    for g in page.get_drawings():
        r = g["rect"]
        if g.get("fill") and max(g["fill"]) < 0.05 and 2 < r.width < 14 and abs(r.width - r.height) < 1:
            xc, yc = 0.5 * (r.x0 + r.x1), 0.5 * (r.y0 + r.y1)
            y = np.polyval(fy, yc); y = 10 ** y if ylog else y
            print(f"x = {np.polyval(fx, xc):.4g}   y = {y:.5g}")


def raster(pdf, out, zoom=4.0):
    import pymupdf
    page = pymupdf.open(pdf)[0]
    page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False).save(out)
    print(out)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "fetch":
        fetch(sys.argv[2], sys.argv[3])
    elif cmd == "markers":
        markers(sys.argv[2], "--ylog" in sys.argv)
    elif cmd == "raster":
        raster(sys.argv[2], sys.argv[3], float(sys.argv[4]) if len(sys.argv) > 4 else 4.0)
