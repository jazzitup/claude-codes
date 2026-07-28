#!/usr/bin/env python3
"""
Find every image referenced inside the theory/exercise markdown of one or
more extract_theory.py JSON outputs -- both `<img src="....svg">` tags and
plain markdown `![alt](....png)` images -- download it, and produce a
high-res white-background PNG (via rsvg-convert for SVGs; raster formats
like .png/.jpg are copied through as-is).

Usage:
    python3 download_diagrams.py <output_dir> <page1.json> [<page2.json> ...]

Produces:
    <output_dir>/diagrams/<original_basename>.png

Only theory-tab images are collected by default (codercise-only diagrams
are usually not wanted in a Theory-tab lecture note); pass --include-exercises
to also pull images that only appear inside exercise content (needed when
also writing up Codercise solutions -- see SKILL.md's "확장 모드").
"""
import re
import os
import sys
import json
import subprocess


def check_tools():
    if subprocess.run(["which", "rsvg-convert"], capture_output=True).returncode != 0:
        print("Missing required tool: rsvg-convert. Install with `brew install librsvg`.", file=sys.stderr)
        sys.exit(1)


def fetch_bytes(url: str) -> bytes:
    from curl_cffi import requests as cffi_requests
    resp = cffi_requests.get(url, impersonate="safari", timeout=30)
    resp.raise_for_status()
    return resp.content


IMG_URL_RE = re.compile(
    r'src="([^"]+\.(?:svg|png|jpe?g))"'   # <img src="...">
    r'|\]\(([^)]+\.(?:svg|png|jpe?g))\)'  # ![alt](...)
)


def collect_image_urls(data: dict, include_exercises: bool) -> set:
    urls = set()
    sections = list(data.get("theories", []))
    if include_exercises:
        sections += list(data.get("exercises", []))
    for s in sections:
        for m in IMG_URL_RE.finditer(s.get("content") or ""):
            urls.add(m.group(1) or m.group(2))
    return urls


if __name__ == "__main__":
    args = sys.argv[1:]
    include_exercises = "--include-exercises" in args
    args = [a for a in args if a != "--include-exercises"]
    if len(args) < 2:
        print("usage: python3 download_diagrams.py [--include-exercises] <output_dir> <page1.json> [...]", file=sys.stderr)
        sys.exit(1)
    check_tools()
    out_dir, json_paths = args[0], args[1:]
    diagrams_dir = os.path.join(out_dir, "diagrams")
    os.makedirs(diagrams_dir, exist_ok=True)

    all_urls = set()
    for p in json_paths:
        data = json.load(open(p, encoding="utf-8"))
        all_urls |= collect_image_urls(data, include_exercises)

    for url in sorted(all_urls):
        base, ext = os.path.splitext(os.path.basename(url))
        ext = ext.lower()
        png_path = os.path.join(diagrams_dir, base + ".png")
        if os.path.exists(png_path):
            print("cached", base + ".png")
            continue
        content = fetch_bytes(url)
        if ext == ".svg":
            svg_path = os.path.join(diagrams_dir, base + ".svg")
            with open(svg_path, "wb") as f:
                f.write(content)
            subprocess.run(
                ["rsvg-convert", "-z", "3", "--background-color=white", "-o", png_path, svg_path],
                check=True,
            )
        else:
            # Raster formats (png/jpg) are already final -- just write them
            # out under the normalized .png name expected by embed_images.py.
            with open(png_path, "wb") as f:
                f.write(content)
        print("downloaded+converted", base + ".png")
