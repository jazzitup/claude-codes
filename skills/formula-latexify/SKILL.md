---
name: formula-latexify
description: >
  Convert a lecture-note HTML file (or a Markdown file that still has
  embedded formula-image PNGs, e.g. from pennylane-codebook-notes) into a
  clean Obsidian-ready Markdown file where every math formula is written
  as native $$...$$ LaTeX instead of a raster image, so it renders in the
  target app's own font via KaTeX/MathJax instead of clashing with it.
  Diagram/portrait images are left as real images. Use when the user asks
  to "라텍스화"/"latexify" a note, convert a "_보강판.html" (or similar
  lecture-note HTML) to ".md" for Obsidian, or fix a markdown note where
  formula images don't match the surrounding font.
  Korean triggers: 수식라텍스화, 라텍스화 해줘, html을 md로 바꾸면서 수식은
  라텍스로, 옵시디언용 노트로 변환, 수식 폰트 안 맞아 고쳐줘.
---

# formula-latexify

HTML(또는 이미 만들어진 markdown) 강의노트에 박혀있는 수식 PNG 이미지를
찾아서, 그 이미지를 실제로 눈으로 읽어(비전) 원본 LaTeX로 옮겨 적고,
`$$...$$` 텍스트로 바꿔치기한다. 다이어그램·인물 사진 등 수식이 아닌
이미지는 그대로 둔다.

## 언제 쓰나

- `Week0X_..._보강판.html` 같은 [[pennylane-codebook-notes]] 산출물을
  Obsidian(또는 다른 KaTeX/MathJax 지원 마크다운 뷰어)용 `.md`로 만들 때.
  이 경우가 기본 시나리오: **입력은 `.html`**, **출력은 `.md`**.
- 이미 `.md`로 변환은 됐는데 수식이 여전히 PNG 이미지인 노트를 나중에
  고칠 때도 같은 파이프라인을 쓴다 (입력이 `.md`인 경우, 아래 2단계에서
  자동으로 다른 경로를 탄다).

왜 필요한가: [[pennylane-codebook-notes]] 파이프라인은 기본적으로 Google
Docs 붙여넣기를 위해 수식을 pdflatex PNG로 렌더링한다. 이 PNG를 그대로
Obsidian 같은 마크다운 앱에 가져가면 본문은 앱의 폰트로, 수식은 Computer
Modern 세리프체 이미지로 나와서 서로 어긋나 보인다. 대신 `$$...$$` LaTeX
원문을 쓰면 그 앱의 KaTeX/MathJax가 알아서 렌더링하므로 폰트가 자연스럽게
맞는다.

## 사전 준비

```bash
python3 -c "import bs4, markdownify" || pip3 install beautifulsoup4 markdownify
```
(둘 다 시스템 python3에 이미 있는 경우가 많다 — 먼저 확인만 하고 없을 때만
설치할 것.)

## 파이프라인

파일 하나당 `<workdir>`를 하나 잡는다 (예: 스크래치패드 아래
`formula-latexify/<노트이름>/`). 여러 파일을 처리할 땐 파일마다 별도
workdir을 쓴다 — 이미지 번호가 파일별로 001부터 다시 시작해야 매니페스트가
꼬이지 않는다.

**1. 수식 추출 + 플레이스홀더 치환 (스크립트)**
```bash
python3 ~/.claude/skills/formula-latexify/scripts/extract_and_placeholder.py \
  --input "<원본.html 또는 .md>" --workdir "<workdir>"
```
- 입력이 `.html`이면: 문서 안의 **모든** base64 `<img>`(수식이든
  아니든)를 일단 찾아서 종류를 셋으로 나눈다:
  - **`formula`** — `class="formula"` 조상을 가진 이미지. `<workdir>/
    formulas/NNN.png`(또는 `.jpg`)로 저장하고 `ZQFORMULAZQNNNZQ` 플레이스홀더로
    바꾼다. Claude가 봐야 한다.
  - **`review`** — `<table>` 안에 있지만 `class="formula"`는 아닌 이미지.
    마찬가지로 저장 + 플레이스홀더 치환하지만, 진짜 수식인지 진짜 그림인지
    애매하므로(아래 "겪은 함정들" 참고) Claude가 하나씩 눈으로 보고 판단해야
    한다.
  - **`diagram`** — 그 외 전부(표 밖에 있고 `class="formula"`도 아님). 진짜
    다이어그램/인물 사진으로 간주하고, **이 스크립트가 바로 그 자리에서
    자동으로 복구**해 최종적으로 `![](data:image/png;base64,...)`로 남는다
    — Claude가 볼 필요도, `manifest.json`에 오를 필요도 없다.
  그런 다음에야 문서 전체를 `markdownify`로 변환한다 — `formula`/`review`
  이미지는 이미 순수 텍스트 플레이스홀더로 바뀌어 있고, `diagram` 이미지도
  변환 직후 원래 base64로 되돌려놓으므로, markdownify가 실제 `<img
  src="data:...">` 태그를 보는 경우 자체가 없다 (아래 "겪은 함정들"의 표
  안 이미지 소실 버그를 이렇게 원천 차단한다).
- 입력이 `.md`이면: 이미 마크다운이므로 markdownify를 타지 않고, `<div
  class="formula">...</div>` 안의 `![](data:image/png;base64,...)`만 정규식으로
  찾아 같은 방식으로 치환한다 (이 경로는 markdownify를 안 타므로 표-소실
  버그 자체가 없다 — `formula` kind만 나온다).
- 결과: `<workdir>/intermediate.md`(다이어그램은 이미 복구된 상태),
  `<workdir>/manifest.json`(Claude가 처리해야 할 `formula`+`review`
  플레이스홀더만, 문서 순서대로, 각 원소에 `kind` 필드 포함),
  `<workdir>/formulas/*.png|jpg`(마찬가지로 `formula`+`review`만).

**중요 — 왜 플레이스홀더를 쓰는가**: `markdownify`(그리고 대부분의
html→md 변환기)는 본문 텍스트 안의 `_`, `*`, `[` 같은 문자를
`\_`처럼 이스케이프한다. LaTeX 원문을 markdownify 이전에 넣으면 백슬래시와
언더스코어가 깨진다. 그래서 markdownify를 통과시키기 전에는 순수
영숫자(`ZQFORMULAZQ007ZQ`)만 넣어두고, markdownify가 다 끝난 **뒤에**
(3단계) 있는 그대로 문자열 치환으로 진짜 LaTeX를 박아넣는다.

**2. 수식 이미지를 직접 읽고 LaTeX로 옮겨 적기 (Claude가 직접, 스크립트 아님)**

`<workdir>/formulas/001.png`부터 순서대로 `Read` 도구로 이미지를 본다.
한 번에 여러 장을 병렬로 Read해도 된다(8~10장씩 묶어서 호출하면 왕복
횟수를 줄일 수 있다). 화면에 보이는 수식을 그대로(줄바꿈·정렬·`\tag{n}`
포함) LaTeX로 옮겨 적는다. 여러 줄로 정렬된 유도 과정(예: `U|\psi\rangle
&= ... \\ &= ...`)은 `\begin{aligned}...\end{aligned}`로 감싸서 `&=` 앞에서
정렬한다. 단순히 두 줄이 나란히 있을 뿐 정렬 의미가 없어도 `aligned`로
감싸는 편이 일관적이고 안전하다.

`manifest.json`의 `kind`가 `"review"`인 항목(표 안에 있지만
`class="formula"`는 아니었던 이미지)은 먼저 그게 진짜 수식인지 진짜
그림인지부터 판단한다 — 예를 들어 "게이트 요약표"에 행렬이 `<img>`로
맨몸으로 박혀있는 경우가 실제로 있었다(작성 단계 실수로 `class="formula"`가
안 붙은 것). 진짜 수식이면 다른 `formula` 항목과 똑같이 LaTeX로 옮겨
적는다. 정말 순수한 그림(사진, 스크린샷 등)이면 옮겨 적지 않고 `latex_bodies.py`의
해당 자리에 리터럴 문자열 `"__IMAGE__"`을 넣는다 — 3단계 스크립트가 원본
이미지를 그대로 복구해 넣는다.

수식 안의 `\tag{n}` 번호는 본문에서 그 번호를 참조하는 텍스트가 있는지
`grep -n '식\s*([0-9])\|Eq\.\s*([0-9])'`로 먼저 확인한다. 참조가 없으면
번호는 굳이 유지하지 않아도 되지만(단순화), 있다면 반드시 유지한다. KaTeX는
`\tag`를 trust 옵션 없이도 지원하므로 Obsidian에서도 그대로 렌더링된다.

이 결과를 `<workdir>/latex_bodies.py`에 저장한다 — 최상위에 `LATEX`라는
리스트, 원소 하나가 `manifest.json`의 원소 하나(문서 순서, 1:1 대응)에
대응한다. 수식이면 raw triple-quoted 문자열(`r"""..."""`)로 써서 백슬래시를
이스케이프할 필요가 없게 하고, `$$` 마커는 넣지 않는다(3단계 스크립트가
붙인다). `review` 중 진짜 그림으로 판단한 항목은 문자열 `"__IMAGE__"`을
그 자리에 넣는다.

```python
# <workdir>/latex_bodies.py 예시
LATEX = [
r"""U|0\rangle = \alpha|0\rangle + \beta|1\rangle""",
r"""\begin{aligned}
X &= \begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix}
\end{aligned}""",
"__IMAGE__",  # review로 분류됐지만 실제로는 표 안의 진짜 사진이었던 경우
]
```

작성 후 `len(LATEX)`가 `manifest.json`의 원소 수와 정확히 같은지 확인한다
(3단계 스크립트가 어차피 검증하지만, 미리 세어보는 편이 빠르다).

**3. 최종 치환 (스크립트)**
```bash
python3 ~/.claude/skills/formula-latexify/scripts/apply_latex.py \
  --intermediate "<workdir>/intermediate.md" \
  --latex "<workdir>/latex_bodies.py" \
  --manifest "<workdir>/manifest.json" \
  --workdir "<workdir>" \
  --output "<최종.md 경로>"
```
`--workdir`는 `"__IMAGE__"` 항목을 복구할 때 `<workdir>/formulas/`에서
원본 이미지를 다시 읽어오는 데 쓰인다. 개수가 안 맞거나 플레이스홀더가 안
남아있으면(중복 소비 등) 에러 메시지와 함께 중단하니, 나온 오류를 보고
`latex_bodies.py`를 고친다.

**4. 검증**

- `grep -c 'ZQFORMULAZQ' <최종.md>`가 0인지 확인 (플레이스홀더가 하나도
  안 남았어야 한다).
- `python3 -c "print(open('<최종.md>').read().count(r'\begin{aligned}'),
  open('<최종.md>').read().count(r'\end{aligned}'))"`로 `aligned` 환경
  개수가 짝이 맞는지 확인.
- 원본 HTML/MD에 있던 다이어그램·인물 사진 개수가 최종 파일에도 그대로
  남아있는지 `grep -c 'data:image/png;base64'`로 원본/최종 비교(수식
  개수만큼 줄어들고 나머지는 그대로여야 한다).
- 가능하면 하나 이상의 수식 블록을 최종 파일에서 발췌해 원본 이미지와
  나란히 눈으로 비교한다.

## 알아둘 것 (겪은 함정들)

- **플레이스홀더 문자셋은 반드시 영문 대문자+숫자만.** `_`, `-`, 공백 등이
  섞이면 markdownify가 이스케이프하거나 markdown 문법으로 오인할 수 있다.
- **`latex_bodies.py`는 raw 문자열(`r"""..."""`)로 쓴다.** 일반 문자열로
  쓰면 `\alpha`의 `\a`가 벨 문자로 해석되는 등 예기치 못한 이스케이프가
  생긴다.
- 원본 노트에 같은 수식(예: 게이트 정의 행렬)이 여러 번 반복 등장해도,
  이 스킬은 매번 별도 이미지로 취급해 각각 다시 옮겨 적는다 — 캐싱하지
  않는다. `render_formulas.py`처럼 해시 기반 캐싱을 추가할 수도 있지만,
  노트 하나에 반복 수식이 수십 개씩 나오는 경우가 아니면 굳이 그럴
  필요는 없었다.
- **`markdownify`는 `<td>` 안에 있는 `<img>`를 아무 경고 없이 통째로
  버린다.** (2026-08-25, Week04·Week07 노트에서 실제로 발견 — "게이트
  요약표"에 `class="formula"` 없이 맨몸 `<img>`로 박힌 행렬 그림들이 있었고,
  처음 버전의 스크립트는 이 이미지들을 손도 안 대고 markdownify에 그대로
  넘겼다가 결과물에서 통째로 사라졌다.) 지금 스크립트는 이걸 원천 차단한다
  — `formula`/`review`/`diagram` 셋으로 분류한 **모든** base64 `<img>`를
  markdownify 실행 **전에** 플레이스홀더로 바꿔치기해서, markdownify가 실제
  `data:` URI가 든 `<img>` 태그를 볼 일 자체가 없게 만든다. `diagram`은
  변환 직후 자동 복구되고, `formula`/`review`는 3단계에서 Claude가 채운다.
  **이미 예전 버전의 스크립트로 만든 결과물이 있다면**, 원본 HTML을
  `grep -c '<td[^>]*>.*<img' `(또는 파이썬으로 `<td>...</td>` 안에 `<img`가
  있는지 검사)로 표 안 이미지 개수를 세어서, 최종 `.md`에 그만큼의 이미지
  (또는 그만큼의 수식)가 실제로 남아있는지 원본과 대조해볼 것.
- `review`로 분류된 표 안 이미지는 진짜 수식인지 진짜 그림인지 반드시 눈으로
  판단해야 한다 — 기계적으로 전부 수식 취급하거나 전부 그림 취급하면 안
  된다. 판단이 애매하면 주변 텍스트(캡션, 셀 헤더)를 같이 읽어서 맥락으로
  판단할 것.
