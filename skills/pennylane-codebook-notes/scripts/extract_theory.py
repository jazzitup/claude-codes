#!/usr/bin/env python3
"""
Fetch a PennyLane Codebook topic page and extract its Theory-tab content
(all accordion sub-sections) plus exercise text, straight from the page's
Next.js RSC data stream -- no headless browser needed.

Usage:
    python3 extract_theory.py <url> <output.json>

Output JSON shape:
{
  "source_url": "...",
  "title": "X and H",
  "summary": "...",
  "learnings": "Learning Objectives:\n* ...",
  "theories": [ {"slug": "...", "title": "...", "content": "<raw markdown incl. $..$ / $$..$$ LaTeX and <img> tags>"} , ...],
  "exercises": [ {"slug": "...", "title": "...", "content": "...", "relatedTheorySlug": "...", "codeTemplate": "..."}, ...]
}

Why this works: PennyLane's site is a Next.js App Router page. The full
topic data (theory markdown, exercises, image URLs) is embedded server-side
in `self.__next_f.push([1, "..."])` RSC stream chunks inside the initial
HTML -- a plain HTTP GET already contains it, it's just chunk-encoded.
A JS-rendering fallback (Playwright) is NOT needed for this site.
"""
import re
import sys
import json


def _install_hint():
    print(
        "Missing dependency: curl_cffi. Install with:\n"
        "  pip install --break-system-packages -U 'curl_cffi>=0.15.0'\n"
        "(or create/activate a venv first).",
        file=sys.stderr,
    )


def fetch_html(url: str) -> str:
    try:
        from curl_cffi import requests as cffi_requests
    except ImportError:
        _install_hint()
        raise
    resp = cffi_requests.get(url, impersonate="safari", timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_rsc_chunks(full: str) -> dict:
    """Decode Next.js Flight (RSC) rows: `<id>:T<hexlen>,<bytes>` for text,
    `<id>:<json...>\\n` for everything else. Lengths for T-rows are UTF-8
    BYTE counts, so all offset arithmetic below happens on the byte buffer."""
    buf = full.encode("utf-8")
    n = len(buf)
    pos = 0
    id_pat = re.compile(rb"([0-9a-f]+):")
    results = {}
    while pos < n:
        m = id_pat.match(buf, pos)
        if not m:
            nl = buf.find(b"\n", pos)
            if nl == -1:
                break
            pos = nl + 1
            continue
        cid = m.group(1).decode()
        rest_start = m.end()
        tm = re.match(rb"T([0-9a-f]+),", buf[rest_start:rest_start + 20])
        if tm:
            length = int(tm.group(1), 16)
            content_start = rest_start + tm.end()
            content = buf[content_start:content_start + length].decode("utf-8", errors="replace")
            results[cid] = content
            pos = content_start + length
        else:
            nl = buf.find(b"\n", rest_start)
            if nl == -1:
                nl = n
            results[cid] = buf[rest_start:nl].decode("utf-8", errors="replace")
            pos = nl + 1
    return results


def find_balanced(s: str, start: int) -> int:
    """Given s[start] == '{', return the index of its matching '}'."""
    depth = 0
    i = start
    in_str = False
    esc = False
    while i < len(s):
        ch = s[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return i
        i += 1
    return -1


def extract_topic(url: str) -> dict:
    html = fetch_html(url)
    # Next.js streams the RSC payload as a series of
    #   self.__next_f.push([1,"<json-escaped chunk>"])
    # calls embedded in <script> tags. Concatenate their decoded bodies.
    pushes = re.findall(r'self\.__next_f\.push\(\[1,(\"(?:[^\"\\]|\\.)*\")\]\)', html, re.S)
    if not pushes:
        raise RuntimeError("no __next_f.push chunks found -- page structure may have changed")
    full = "".join(json.loads(p) for p in pushes)
    results = parse_rsc_chunks(full)

    target_key = None
    for k, v in results.items():
        if '"getCodebookTopic"' in v and '"theories"' in v:
            target_key = k
            break
    if target_key is None:
        raise RuntimeError("topic data chunk not found -- page structure may have changed")

    raw = results[target_key]
    idx = raw.find('"codebookModule"')
    topic_start = raw.find('"topic":{', idx)
    if topic_start == -1:
        raise RuntimeError('"topic" key not found in codebookModule data')
    brace_open = raw.find("{", topic_start)
    brace_close = find_balanced(raw, brace_open)
    topic = json.loads(raw[brace_open:brace_close + 1])

    theories = []
    for t in topic.get("theories", []):
        content_ref = t["content"]
        if isinstance(content_ref, str) and content_ref.startswith("$"):
            content_md = results.get(content_ref[1:], "")
        else:
            content_md = content_ref
        theories.append({"slug": t["slug"], "title": t["title"], "content": content_md})

    exercises = []
    for e in topic.get("exercises", []):
        content_ref = e.get("content")
        if isinstance(content_ref, str) and content_ref.startswith("$") and content_ref[1:].isalnum():
            content_md = results.get(content_ref[1:], content_ref)
        else:
            content_md = content_ref
        template_ref = e.get("codeTemplate")
        if isinstance(template_ref, str) and template_ref.startswith("$") and template_ref[1:].isalnum():
            template = results.get(template_ref[1:], template_ref)
        else:
            template = template_ref

        exercises.append({
            "slug": e.get("slug"),
            "title": e.get("title"),
            "content": content_md,
            "relatedTheorySlug": e.get("relatedTheorySlug"),
            "codeTemplate": template,
        })

    return {
        "source_url": url,
        "title": topic.get("title"),
        "summary": topic.get("summary"),
        "learnings": topic.get("learnings"),
        "theories": theories,
        "exercises": exercises,
    }


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python3 extract_theory.py <url> <output.json>", file=sys.stderr)
        sys.exit(1)
    url, out_path = sys.argv[1], sys.argv[2]
    data = extract_topic(url)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("OK", out_path, "title:", data["title"], "theories:", [t["title"] for t in data["theories"]])
