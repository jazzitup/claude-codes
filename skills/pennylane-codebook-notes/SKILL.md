---
name: pennylane-codebook-notes
description: >
  Generate a detailed Korean lecture note (Google-Docs-paste-ready HTML,
  formulas and diagrams rendered as real images) from one or more PennyLane
  Codebook topic pages, by reading every Theory-tab accordion sub-section
  (What will you learn?, and each named theory section) in full. Use when
  the user gives PennyLane Codebook URLs (pennylane.ai/codebook/...) and
  asks for a lecture note / 강의노트 / summary of the Theory content.
  Korean triggers: 페니레인 코드북, PennyLane 강의노트, 이론 탭 정리,
  codebook 이론 읽어서 노트 만들어줘.
---

# PennyLane Codebook → 강의노트 생성기

이 스킬은 PennyLane Codebook 토픽 페이지들의 **Theory 탭**(하위 아코디언 섹션
전부: "What will you learn?" + 각 이론 섹션)을 읽어서, 수식과 다이어그램을
실제 이미지로 렌더링한 뒤, Google Docs에 그대로 복사-붙여넣기 할 수 있는
자기완결형(self-contained) HTML 강의노트를 만든다.

## 왜 headless 브라우저가 필요 없는가

PennyLane Codebook은 Next.js App Router 사이트다. Theory 탭의 전체 마크다운
원문(LaTeX 수식 포함, `<img>` 태그 포함)은 서버에서 이미 렌더된 첫 HTTP 응답
안에 Next.js RSC(React Server Components) 스트림 형태로 박혀 있다 —
`self.__next_f.push([1,"..."])` 형태의 청크들. `scripts/extract_theory.py`가
이 스트림을 직접 파싱해서 원문을 그대로 뽑아낸다. Playwright/헤드리스
크롬은 필요 없다 (처음 시도했을 때는 이 사실을 모르고 렌더링 우회를
시도하다 시간을 많이 썼다 — 반복하지 말 것).

## 사전 준비 (매 실행 전 1회)

```bash
mkdir -p <workdir>   # 예: 스크래치패드 아래 pennylane-notes/<날짜>
source ~/.claude/skills/pennylane-codebook-notes/scripts/setup_env.sh <workdir>
```

이 스크립트는 `<workdir>/venv`에 `curl_cffi`를 설치하고, `pdflatex` /
`pdfcrop` / `pdftoppm` (TeX Live/MacTeX) / `rsvg-convert` (`brew install
librsvg`) 존재 여부를 확인한다. 시스템 도구가 없으면 경고만 출력하고
계속 진행하니, 경고가 뜨면 먼저 설치부터 안내할 것.

## 파이프라인 (URL 목록만 바뀐다)

사용자가 준 URL마다 다음을 반복한다. `<workdir>`는 고정, `<slug>`는 URL
마지막 경로 조각(예: `x-and-h`).

**1. 원문 추출** — 각 URL에 대해:
```bash
python3 ~/.claude/skills/pennylane-codebook-notes/scripts/extract_theory.py \
  "<url>" "<workdir>/<slug>.json"
```
출력 JSON에는 `title`, `summary`, `learnings`("What will you learn?" 내용),
그리고 `theories`(슬러그별 원문 마크다운+LaTeX 배열), `exercises`가 들어있다.
**이 JSON을 Read 도구로 직접 읽고 내용을 파악한다** — 강의노트를 쓰는 것은
스크립트가 아니라 Claude의 몫이다.

**2. 수식 렌더링** (모든 JSON을 한 번에 넘겨도 됨, 중복 수식은 캐싱됨):
```bash
python3 ~/.claude/skills/pennylane-codebook-notes/scripts/render_formulas.py \
  "<workdir>" "<workdir>"/*.json
```
`<workdir>/formulas/<hash>.png` 파일들과, 어떤 수식이 어떤 파일이 됐는지
알려주는 `<workdir>/formula_mapping.json`이 생성된다. 이 매핑 파일을 Read로
읽어서 HTML을 쓸 때 `<img src="__IMG__/<hash>.png">` 형태로 정확한 파일명을
참조한다.

**3. 다이어그램(회로도 등 SVG) 다운로드+변환**:
```bash
python3 ~/.claude/skills/pennylane-codebook-notes/scripts/download_diagrams.py \
  "<workdir>" "<workdir>"/*.json
```
`<workdir>/diagrams/<원래파일명>.png`가 생성된다. 기본적으로 Theory 탭
안에서 참조되는 이미지만 가져온다(코더사이즈 전용 그림은 제외). 코더사이즈
그림도 필요하면 `--include-exercises` 플래그를 앞에 붙인다.

**4. 강의노트 본문 작성 (Claude가 직접, 스크립트 아님)**

`templates/style_block.txt`를 그대로 `<head>`에 넣고,
`templates/skeleton.html`의 클래스 어휘를 따라 본문을 작성한다:

- `.toc` — 목차
- `h2 > span.num` — "TOPIC 01" 같은 배지 + 토픽 제목
- `.goalbox` — 그 토픽의 "What will you learn?" 학습목표
- `h3` — Theory 탭의 각 아코디언 하위 섹션 (반드시 전부 펼쳐서 순서대로)
- `.formula > img` — `$$...$$` 블록마다 하나씩, 원문 순서 그대로
- `.figure > img + .cap` — 다이어그램 + 한국어 캡션
- `.exbox` / 안의 `.solbox` — 이론 본문에 인라인으로 나오는 "Exercise
  I.x.y"(및 그 안의 `<details>Solution` 풀이). **코더사이즈(코딩 실습) 탭
  자체는 넣지 않는다** — 사용자가 명시적으로 요청하지 않는 한 Theory 탭
  범위만 다룬다.
- `.divider` — 토픽 사이 구분선
- `table.summary` — 필요하면 마지막에 정리표

번역/설명은 원문에 충실하되(수식·정의를 임의로 바꾸지 않는다) 아주
상세하게 풀어 쓴다. 원문에 있는 모든 하위 섹션과 인라인 연습문제·풀이를
빠짐없이 포함한다 — 일부만 요약하지 말 것.

이 본문을 `<workdir>/lecture_src.html`로 저장한다(이미지는 전부
`src="__IMG__/파일명"` placeholder로).

**5. 이미지 base64 임베드**:
```bash
python3 ~/.claude/skills/pennylane-codebook-notes/scripts/embed_images.py \
  "<workdir>/lecture_src.html" "<workdir>" "<workdir>/lecture_final.html"
```
`MISSING` 경고가 뜨면 파일명 오타이니 반드시 0건이 될 때까지 고칠 것.

**6. 산출물 전달**

- `Artifact` 도구로 `lecture_final.html`을 발행한다 (favicon은 주제에 맞는
  이모지 1~2개, title은 강의노트 제목). `<title>`/`<head>`/`<body>` 태그를
  직접 넣지 않는다 — style_block.txt와 본문만 있으면 된다.
- `SendUserFile`로 같은 파일을 첨부해서, 사용자가 브라우저로 열어 전체
  선택→복사→Google Docs 붙여넣기 할 수 있게 안내한다.

## 알아둘 것 (오늘 겪은 함정들)

- `align*` 환경을 `varwidth`(standalone 클래스)와 같이 쓰면 한쪽에 큰 여백이
  생기는 TeX 버그가 있다 → `render_formulas.py`가 이미 `pdfcrop`으로
  해결해뒀다. 새로 손대지 않는 한 신경 쓸 필요 없음.
- 원문 마크다운에는 `\end{align*} \tag{n}`처럼 MathJax는 허용하지만 진짜
  LaTeX(amsmath)는 거부하는 패턴이 종종 나온다 → 이미 정규식으로 제거됨.
- RSC 청크의 `T<hexlen>,` 길이는 **UTF-8 바이트 길이**다. 문자 단위로
  슬라이싱하면 유니코드 문자(켓 기호 등) 때문에 오프셋이 어긋난다 →
  `extract_theory.py`는 항상 바이트 버퍼에서 자른다.
- 페이지 구조가 바뀌어 `extract_theory.py`가 `RuntimeError`를 던지면,
  최신 페이지의 `self.__next_f.push` 청크를 다시 눈으로 훑어서 `topic` 키
  경로가 바뀌었는지 확인할 것 (`"getCodebookTopic"` 문자열로 검색하면
  빠르게 찾을 수 있다).
