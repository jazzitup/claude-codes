#!/usr/bin/env python3
"""Overleaf에서 받은 소스 폴더로 저널 투고용 소스 꾸러미를 만든다.

하는 일
  1. .tex에서 주석을 지운다 (주석만 있는 줄은 줄째 삭제, 코드 뒤 주석은 잘라냄,
     줄 끝의 맨 '%'는 공백 억제용이므로 그대로 둠).
  2. 어디에서도 쓰이지 않는 한 줄짜리 \\newcommand/\\def 정의를 지운다 (--keep-macros로 끔).
  3. 연속된 빈 줄을 하나로 줄인다.
  4. .tex가 실제로 부르는 그림과 .bib만 출력 폴더로 복사한다.
  5. 그림 경로의 하위 폴더를 없애 모두 같은 폴더에 둔다 (--no-flatten으로 끔).
  6. 원본과 결과를 각각 임시 폴더에서 컴파일해 쪽수와 본문 텍스트가 같은지 비교한다
     (--no-compile로 끔). 출력 폴더에는 빌드 산출물을 남기지 않는다.

예
  make_submission.py --src ~/Downloads/unzipped --tex main_v2.tex \\
      --out "submission Nov 24 2026" --name main_v2_sub.tex
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

IMG_EXTS = [".pdf", ".png", ".jpg", ".jpeg", ".eps", ".PDF", ".PNG", ".JPG", ".JPEG"]
DEF_RE = re.compile(r"^\s*\\(?:re)?newcommand\*?\{?\\([A-Za-z@]+)\}?|^\s*\\def\\([A-Za-z@]+)")
RENEW_RE = re.compile(r"^\s*\\renewcommand")
GFX_RE = re.compile(r"(\\includegraphics\s*(?:\[[^\]]*\])?\s*\{)([^}]*)(\})")


def comment_pos(line):
    """이스케이프되지 않은 첫 '%'의 위치. 없으면 -1."""
    for i, c in enumerate(line):
        if c == "%":
            j, n = i - 1, 0
            while j >= 0 and line[j] == "\\":
                n += 1
                j -= 1
            if n % 2 == 0:
                return i
    return -1


def balanced(s):
    depth, i = 0, 0
    while i < len(s):
        if s[i] == "\\":
            i += 2
            continue
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
        i += 1
    return depth == 0


def strip_tex(src, keep_macros=False):
    lines = src.split("\n")
    stats = {"full": 0, "trail": 0, "bare_kept": 0, "macros": []}
    # 1) 주석
    kept = []
    for l in lines:
        p = comment_pos(l)
        if p < 0:
            kept.append(l)
            continue
        if l[:p].strip() == "":
            stats["full"] += 1
            continue
        if l[p + 1:].strip() == "":
            stats["bare_kept"] += 1
            kept.append(l)
        else:
            stats["trail"] += 1
            kept.append(l[:p].rstrip())
    # 2) 안 쓰는 매크로 (프리앰블의 한 줄짜리 정의만)
    if not keep_macros:
        bd = next((i for i, l in enumerate(kept) if "\\begin{document}" in l), len(kept))
        changed = True
        while changed:  # 서로만 참조하는 매크로까지 걷어내려고 반복
            changed = False
            for i in range(bd):
                l = kept[i]
                if l is None:
                    continue
                m = DEF_RE.match(l)
                if not m or RENEW_RE.match(l):
                    continue
                name = m.group(1) or m.group(2)
                if "@" in name or not balanced(l):
                    continue
                use = re.compile(r"\\" + re.escape(name) + r"(?![A-Za-z@])")
                others = [x for k, x in enumerate(kept) if k != i and x is not None]
                own_def = re.compile(r"^\s*\\(?:re)?newcommand\*?\{?\\" + re.escape(name) + r"(?![A-Za-z@])|^\s*\\def\\" + re.escape(name) + r"(?![A-Za-z@])")
                if any(use.search(x) and not own_def.match(x) for x in others):
                    continue
                stats["macros"].append(name)
                kept[i] = None
                changed = True
            if changed:
                kept = [x for x in kept if x is not None]
                bd = next((i for i, l in enumerate(kept) if "\\begin{document}" in l), len(kept))
    out = "\n".join(kept)
    out = re.sub(r"\n{3,}", "\n\n", out).lstrip("\n")
    return out, stats


def resolve_figure(src_dir, path):
    cand = os.path.join(src_dir, path)
    if os.path.isfile(cand):
        return path
    for e in IMG_EXTS:
        if os.path.isfile(cand + e):
            return path + e
    return None


def compile_dir(d, tex):
    r = subprocess.run(["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", tex],
                       cwd=d, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
    base = os.path.splitext(tex)[0]
    pdf = os.path.join(d, base + ".pdf")
    log = ""
    lp = os.path.join(d, base + ".log")
    if os.path.isfile(lp):
        log = open(lp, errors="replace").read()
    info = {"ok": r.returncode == 0 and os.path.isfile(pdf), "pdf": pdf,
            "errors": len(re.findall(r"^!", log, re.M)),
            "undefined": len(re.findall(r"LaTeX Warning: (?:Reference|Citation).*undefined", log)),
            "missing_files": re.findall(r"File `([^']+)' not found", log)}
    blg = os.path.join(d, base + ".blg")
    info["bib_warnings"] = re.findall(r"^Warning--(.*)$", open(blg, errors="replace").read(), re.M) if os.path.isfile(blg) else []
    if info["ok"]:
        pi = subprocess.run(["pdfinfo", pdf], stdout=subprocess.PIPE, text=True).stdout
        m = re.search(r"Pages:\s+(\d+)", pi)
        info["pages"] = int(m.group(1)) if m else None
        info["text"] = subprocess.run(["pdftotext", pdf, "-"], stdout=subprocess.PIPE, text=True, errors="replace").stdout
    else:
        info["tail"] = "\n".join(r.stdout.splitlines()[-15:])
    return info


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True, help="Overleaf zip을 푼 폴더")
    ap.add_argument("--tex", required=True, help="원본 .tex 파일 이름 (src 기준)")
    ap.add_argument("--out", required=True, help="투고 꾸러미를 만들 폴더 (비어 있어야 함)")
    ap.add_argument("--name", help="결과 .tex 파일 이름 (기본: <원본>_sub.tex)")
    ap.add_argument("--keep-macros", action="store_true", help="안 쓰는 매크로 정의를 지우지 않음")
    ap.add_argument("--no-flatten", action="store_true", help="그림의 하위 폴더 구조를 유지")
    ap.add_argument("--no-compile", action="store_true", help="컴파일 비교를 건너뜀")
    a = ap.parse_args()

    src_dir = os.path.abspath(os.path.expanduser(a.src))
    out_dir = os.path.abspath(os.path.expanduser(a.out))
    tex_path = os.path.join(src_dir, a.tex)
    if not os.path.isfile(tex_path):
        sys.exit(f"원본 .tex가 없음: {tex_path}")
    os.makedirs(out_dir, exist_ok=True)
    if [f for f in os.listdir(out_dir) if not f.startswith(".")]:
        sys.exit(f"출력 폴더가 비어 있지 않음: {out_dir}")
    name = a.name or (os.path.splitext(os.path.basename(a.tex))[0] + "_sub.tex")

    src = open(tex_path, encoding="utf-8").read()
    sub, st = strip_tex(src, a.keep_macros)

    # 그림
    problems, copies, seen = [], {}, {}
    def repl(m):
        ref = m.group(2).strip()
        real = resolve_figure(src_dir, ref)
        if real is None:
            problems.append(f"그림 파일 없음: {ref}")
            return m.group(0)
        dest = real if a.no_flatten else os.path.basename(real)
        if seen.setdefault(dest, real) != real:
            problems.append(f"이름 충돌(평탄화 불가): {real} vs {seen[dest]}")
            return m.group(0)
        copies[real] = dest
        new_ref = dest if os.path.splitext(ref)[1] else os.path.splitext(dest)[0]
        return m.group(1) + new_ref + m.group(3)
    sub = GFX_RE.sub(repl, sub)

    # bib, bst, \input
    extra = []
    for m in re.finditer(r"\\bibliography\{([^}]*)\}", sub):
        for b in m.group(1).split(","):
            b = b.strip()
            f = b if b.endswith(".bib") else b + ".bib"
            if os.path.isfile(os.path.join(src_dir, f)):
                extra.append(f)
            else:
                problems.append(f".bib 파일 없음: {f}")
    for m in re.finditer(r"\\bibliographystyle\{([^}]*)\}", sub):
        f = m.group(1).strip() + ".bst"
        if os.path.isfile(os.path.join(src_dir, f)):
            extra.append(f)
    for m in re.finditer(r"\\(?:input|include)\{([^}]*)\}", sub):
        problems.append(f"\\input/\\include는 처리하지 않음 — 직접 확인: {m.group(1)}")
    if re.search(r"\\graphicspath", sub):
        problems.append("\\graphicspath가 있음 — 그림 경로를 직접 확인할 것")
    non_ascii = sorted({d for d in list(copies.values()) + [name] if re.search(r"[^\x00-\x7F]", d)})
    for d in non_ascii:
        problems.append(f"ASCII가 아닌 파일명: {d}")

    if any(p.startswith(("그림 파일 없음", "이름 충돌", ".bib 파일 없음")) for p in problems):
        print("\n".join("문제: " + p for p in problems))
        sys.exit("중단: 위 문제를 먼저 해결할 것 (출력 폴더에는 아무것도 쓰지 않았음)")

    open(os.path.join(out_dir, name), "w", encoding="utf-8").write(sub)
    for real, dest in copies.items():
        os.makedirs(os.path.dirname(os.path.join(out_dir, dest)), exist_ok=True)
        shutil.copy2(os.path.join(src_dir, real), os.path.join(out_dir, dest))
    for f in dict.fromkeys(extra):
        shutil.copy2(os.path.join(src_dir, f), os.path.join(out_dir, os.path.basename(f)))

    used = set(copies) | set(extra) | {a.tex}
    unused = []
    for root, _, files in os.walk(src_dir):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), src_dir)
            if rel not in used and not f.startswith("."):
                unused.append(rel)

    print(f"결과 .tex : {os.path.join(out_dir, name)}")
    print(f"줄 수     : {len(src.splitlines())} -> {len(sub.splitlines())}")
    print(f"주석      : 줄째 삭제 {st['full']}, 코드 뒤 주석 삭제 {st['trail']}, 줄 끝 '%' 유지 {st['bare_kept']}")
    print(f"매크로    : 안 쓰는 정의 {len(st['macros'])}개 삭제" + (f" ({', '.join(st['macros'])})" if st["macros"] else ""))
    print(f"그림      : {len(copies)}개 복사" + ("" if a.no_flatten else " (하위 폴더 없이 같은 폴더에)"))
    print(f"그 밖     : {', '.join(dict.fromkeys(extra)) or '없음'}")
    print(f"뺀 파일   : {len(unused)}개" + (f" ({', '.join(sorted(unused))})" if unused else ""))
    for p in problems:
        print("주의: " + p)

    if a.no_compile:
        return
    if not shutil.which("latexmk"):
        print("주의: latexmk가 없어 컴파일 비교를 건너뜀")
        return
    tmp = tempfile.mkdtemp(prefix="subpkg_")
    try:
        o = os.path.join(tmp, "orig"); n = os.path.join(tmp, "new")
        shutil.copytree(src_dir, o); shutil.copytree(out_dir, n)
        ro, rn = compile_dir(o, a.tex), compile_dir(n, name)
        for label, r in (("원본", ro), ("결과", rn)):
            if r["ok"]:
                print(f"컴파일 {label}: 성공, {r['pages']}쪽, 에러 {r['errors']}, 미해결 참조·인용 {r['undefined']}")
            else:
                print(f"컴파일 {label}: 실패\n{r.get('tail','')}")
            for w in r["bib_warnings"]:
                print(f"  BibTeX 경고({label}): {w}")
        if ro["ok"] and rn["ok"]:
            same = ro["text"] == rn["text"]
            print("PDF 본문 텍스트 비교: " + ("같음" if same else "다름 — 확인 필요"))
            if not same or ro["pages"] != rn["pages"]:
                sys.exit(1)
        else:
            sys.exit(1)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
