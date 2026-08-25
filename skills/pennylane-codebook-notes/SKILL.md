---
name: pennylane-codebook-notes
description: >
  Generate a detailed Korean lecture note from one or more PennyLane
  Codebook topic pages, by reading every Theory-tab accordion sub-section
  (What will you learn?, and each named theory section) in full. Default
  output is Google-Docs-paste-ready HTML with formulas and diagrams
  rendered as real images; if the target is Obsidian or another
  markdown/KaTeX renderer, formulas are written as raw $$...$$ LaTeX
  instead (diagrams still images) — see the "출력 대상이 Obsidian/마크다운일
  때" section. Use when the user gives PennyLane Codebook URLs
  (pennylane.ai/codebook/...) and asks for a lecture note / 강의노트 /
  summary of the Theory content. Korean triggers: 페니레인 코드북, PennyLane
  강의노트, 이론 탭 정리, codebook 이론 읽어서 노트 만들어줘.
---

# PennyLane Codebook → 강의노트 생성기

이 스킬은 PennyLane Codebook 토픽 페이지들의 **Theory 탭**(하위 아코디언 섹션
전부: "What will you learn?" + 각 이론 섹션)을 읽어서, 수식과 다이어그램을
실제 이미지로 렌더링한 뒤, Google Docs에 그대로 복사-붙여넣기 할 수 있는
자기완결형(self-contained) HTML 강의노트를 만든다.

## 출력 대상이 Obsidian/마크다운일 때 — 수식을 이미지로 만들지 않는다

아래 파이프라인 전체(특히 2단계 `render_formulas.py`, 5단계
`embed_images.py`)는 **Google Docs가 LaTeX를 직접 렌더링하지 못한다는
전제**로 수식을 pdflatex PNG로 박아넣는다. 하지만 사용자가 "옵시디언용",
".md로 줘", "노트 앱에 붙여넣을 거야"처럼 대상이 Obsidian이나 다른
마크다운 뷰어(KaTeX/MathJax 내장)임을 밝히면 얘기가 다르다 — 그런 뷰어는
`$$...$$`(display) / `$...$`(inline) LaTeX 원문을 그 자체로 렌더링하므로:

- **수식은 2·5단계를 건너뛰고 `.formula` 안에 `$$...$$` 원문 LaTeX를 그대로
  쓴다.** 수식 번호가 필요하면 `\tag{n}`도 그대로 유지 — KaTeX는 `\tag`를
  trust 옵션 없이도 지원한다.
- **다이어그램(회로도, Bloch 구 등 실제 그림)은 그대로 이미지로 받아 넣는다**
  — 3단계(`download_diagrams.py`)는 그대로 쓴다. 이미지가 필요한 건 수식이
  아니라 진짜 그림이다.
- 왜 중요한가 (2026-08-25 실제로 겪은 문제): Google-Docs용으로 만든 HTML
  노트를 나중에 Obsidian `.md`로 변환했더니, pdflatex로 그려진 수식 PNG의
  세리프체(Computer Modern)가 Obsidian 본문의 산세리프 폰트와 완전히
  어긋나 보였다. 이미 이미지로 박힌 노트를 고치려면 PNG 50개를 하나하나
  눈으로 읽어 LaTeX로 옮겨 적어야 했다 — 처음부터 대상이 Obsidian이었다면
  이 작업 자체가 필요 없었다. **출력 형식은 사후에 바꾸기보다, 시작 시점에
  대상(Google Docs vs. 마크다운 앱)을 먼저 확인하고 그에 맞는 파이프라인을
  타는 것이 낫다.**

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

PennyLane Codebook 자체는 curl_cffi로 직접 요청해도 막히지 않는 사이트이므로
(2026-07-28 기준, Prepare Yourself·Measurements·Circuits-with-Many-Qubits
모듈 전부에서 확인됨), 기본적으로는 `insane-search` 스킬 없이 위 스크립트만으로
충분하다. 다만 `extract_theory.py`가 403/차단성 에러로 실패하는 경우에는
`insane-search` 스킬을 fallback으로 호출해 페이지 원문을 가져올 것 — 단 이
경로로 얻은 텍스트는 서버 렌더링된 MathJax 결과물이라 원본 LaTeX 소스가 아닐
수 있으므로, 수식은 눈으로 보이는 대로 다시 LaTeX로 옮겨 써야 할 수 있다는
점을 감안한다.

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
`<workdir>/diagrams/<원래파일명>.png`가 생성된다. `<img src="...">` 태그와
마크다운 `![](....png)` 형태 이미지 링크를 모두 잡아내고, svg는 rsvg-convert로
변환하고 png/jpg는 그대로 받아온다. 기본적으로 Theory 탭 안에서 참조되는
이미지만 가져온다(코더사이즈 전용 그림은 제외). 코더사이즈 그림도 필요하면
(아래 "확장 모드" 참고) `--include-exercises` 플래그를 앞에 붙인다.

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
빠짐없이 포함한다 — 일부만 요약하지 말 것. "자세히", "detailed" 같은 요청이
없어도 이 상세함이 기본값이다 — 절대 요약판으로 축약하지 말 것.

표 안에 들어있는 인라인 `$...$` 수식(예: 게이트 총정리표의 행렬)은
`render_formulas.py`가 잡아내는 `$$...$$` 블록이 아니므로 별도로 렌더링해야
한다. `~/.claude/skills/pennylane-codebook-notes/scripts/render_formulas.py`의
`render_formula(latex, workdir)` 함수를 그대로 import해서, 표에 필요한 LaTeX
문자열들만 모은 짧은 스크립트를 `<workdir>`에 임시로 작성해 실행하면 같은
캐싱된 `<workdir>/formulas/` 디렉토리에 결과가 쌓인다 (여러 토픽에 같은 게이트
표가 반복되면 이전 워크디렉토리에서 만든 PNG를 그대로 복사해 재사용해도 된다).

### 확장 모드 — Codercise(코딩 실습) 문제와 해답까지 포함하기

사용자가 "연습문제도 다 풀어줘", "코더사이즈 해답까지", "아주 자세히" 등으로
명시적으로 요청하면, Theory 탭 범위를 벗어나 각 이론 절에 딸린 Codercise
(`exercises` 배열)까지 노트에 포함하고, 문제마다 **직접 작성한 해답 코드와
설명**을 덧붙인다. 이때 유의할 점:

- **PennyLane 코드북은 코더사이즈에 공식 해답을 제공하지 않는다.** 따라서
  이 해답은 코드북 공식 풀이가 아니라 스스로 구성한 풀이임을 노트 서두에
  명시할 것.
- 문제 본문에 회로 다이어그램(`<img>` 그림)이 있으면, 3단계에서
  `--include-exercises` 플래그를 켜서 그 그림도 함께 내려받고, `Read`
  도구로 실제로 그림을 눈으로 봐서 회로 구조를 파악한 뒤 해답을 작성한다
  (텍스트 설명만으로 회로를 추측하지 말 것 — 제어점의 색이 채워졌는지
  비었는지, 게이트 순서 등은 그림을 봐야 정확히 알 수 있다).
- 문제 박스(`.exbox`/`.solbox`와는 별개의) 스타일로 `.codercise`(문제 전체를
  감싸는 박스)와 그 안의 `.answer`(해답, `.solbox`와 같은 톤이지만 별도
  클래스)를 새로 정의해서 쓴다 — 기존 `templates/style_block.txt`에는 없으므로
  이 노트를 작성하는 HTML의 `<style>` 블록에 직접 추가한다 (색상 변수는
  `--exercise*`/`--solution*` 패턴을 따라 `--answer*` 계열로 새로 정의).
- 해답 코드는 실제로 동작하는 완전한 PennyLane 코드로 쓴다 (import, device
  생성 포함). 초안을 쓰다가 실수를 바로잡았다고 해서 잘못된 초안을 코드
  블록에 남겨두지 말 것 — 최종적으로 맞는 버전 하나만 깔끔하게 제시한다.
- 이 모드가 아닐 때는 원래 규칙대로 Codercise를 넣지 않는다 — 매번 자동으로
  켜지는 기본값이 아니라, 명시적 요청이 있을 때만 켜는 옵션이다.

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
- **`lecture_final.html`을 현재 프로젝트 작업 디렉토리(cwd)로도 복사해 둔다**
  (`cp <workdir>/lecture_final.html <cwd>/<설명적인-파일명>.html`). 스크래치패드는
  세션이 끝나면 사라지므로, 사용자가 매번 채팅 첨부파일을 다시 내려받지 않아도
  되도록 프로젝트 디렉토리에 영구 사본을 남긴다. 같은 프로젝트에서 여러 노트를
  만들 경우 이전 파일을 덮어쓰지 않도록 토픽을 반영한 파일명을 쓴다(예:
  `lecture_week3_circuits_many_qubits.html`).

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
- 본문 HTML에 원문의 인라인 `$...$` LaTeX를 그대로 텍스트로 남겨두면 안 된다
  (`$|\psi\rangle$`처럼 달러 기호·백슬래시가 그대로 노출됨). 짧은 심볼(α, β,
  |0⟩, ⟨φ|ψ⟩ 등)은 유니코드 문자로 바꿔 쓰고, 표시용 수식(`$$...$$`)만 이미지로
  렌더링한다.
- `download_diagrams.py`는 원래 `<img src="....svg">` 태그만 잡아냈는데,
  코드북 본문에는 마크다운 `![](....png)` 형태로 들어간 순수 PNG 그림(예:
  Measurements 노드의 projection.png)도 있어 놓치는 경우가 있었다 → 스크립트를
  고쳐서 `<img>`/마크다운 두 형태 모두, svg 외에 png/jpg도 잡아내도록 함.
  더 이상 수동으로 `curl`을 따로 돌릴 필요 없음.
- 셸이 이상하게 멈추면(간단한 `echo`조차 응답 없음) 먼저 사용자의 셸
  프로필(`~/.bash_profile`, `~/.zshrc` 등)에 인터랙티브 서브셸을 여는 명령
  (예: 그냥 `bash`라고만 적힌 줄)이 들어있지 않은지 확인할 것 — Bash 도구
  자체의 문제가 아니라 프로필이 non-TTY 환경에서 새 셸을 열고 무한 대기하는
  경우였다.
