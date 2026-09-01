---
name: pennylane-quiz-handout
description: >
  Build a print-ready, hand-written-answer quiz (.md) from one or more
  PennyLane Codebook Codercises, verbatim, for the "quantum_computing_class"
  course (Sejong University, Prof. Yongsun Kim). The official problem prose
  is translated to Korean (math kept as LaTeX), the official starter code
  (docstring, comments, "YOUR CODE HERE" stub) is copied byte-for-byte
  unmodified, and blank lines (~2x the expected solution length, 5-10 lines)
  are inserted after "YOUR CODE HERE" for students to write answers by hand
  on a printed page. Saved into the course's Google Drive "quiz" folder.
  Use when the user asks to "퀴즈 만들어줘" / "Codercise ... 를 그대로 퀴즈로
  내줘" / "인쇄용 퀴즈 만들어줘" / "이번 주 코더사이즈로 시험문제 내줘",
  naming specific Codercise numbers (e.g. I.1.1, I.1.2) and a course
  notebook/codebook page URL.
---

# PennyLane Codercise → 손글씨 답안용 인쇄 퀴즈 (.md)

2026-09-01에 Quiz #1 (Codercise I.1.1, I.1.2)을 만들면서 확립한 과정.
실제로 만든 파일: `quiz/Quiz1_2026-09-03.md` (Google Drive `수업 2026 fall/quiz/` 폴더).

## 0. 이 스킬이 하는 일 / 안 하는 일

- **한다**: 지정된 Codercise 번호들의 **공식 문제 원문 + 스타터 코드**를 정확히
  가져와서, 문제 설명은 한글로 번역하고(수식은 LaTeX), 코드는 원문 그대로
  복사해서, 학생이 종이에 손으로 답을 쓸 수 있는 빈 줄이 있는 퀴즈 `.md`를
  만든다.
- **안 한다**: 문제를 풀어서 정답을 채워 넣지 않는다 (`pennylane-codercise-notebook`
  스킬과 반대 — 그 스킬은 정답 코드를 완성해서 실행 가능한 노트북을 만드는
  것이고, 이 스킬은 빈칸 있는 시험지를 만드는 것이다). Codercise 코드/설명을
  임의로 지어내지 않는다 — 공식 원문에 없는 내용은 쓰지 않는다.

## 1. 공식 문제 원문 + 코드 템플릿 가져오기

`pennylane.ai/codebook/...` 페이지는 Next.js SPA라 `WebFetch`로는 제목만
나온다. 두 가지 방법이 있다:

**우선순위 1순위 — `pennylane-codebook-notes` 스킬의 추출 스크립트** (더 빠르고
안정적, RSC 스트림을 직접 파싱):
```bash
mkdir -p <workdir>
source ~/.claude/skills/pennylane-codebook-notes/scripts/setup_env.sh <workdir>
source <workdir>/venv/bin/activate
python3 ~/.claude/skills/pennylane-codebook-notes/scripts/extract_theory.py \
  "<codebook 모듈 URL>" "<workdir>/<slug>.json"
```
결과 JSON의 `exercises[]`에 `title`(공식 제목), `content`(문제 원문),
`codeTemplate`(스타터 코드)이 들어있다.

**우선순위 2순위 — Chrome DevTools MCP로 직접 렌더링 확인** (2026-09-01에 이
방법으로 I.1.1/I.1.2를 성공적으로 가져옴; 위 스크립트가 안 되거나 검증하고
싶을 때):
```
mcp__chrome-devtools__new_page(url="<codebook 모듈 URL>")
mcp__chrome-devtools__wait_for(text=["Codercise I.X.Y", "<함수명>"])
mcp__chrome-devtools__take_snapshot()   # 접힌 코더사이즈는 button uid를 click()으로 펼친 뒤 재스냅샷
```
스냅샷의 `textbox ... value="..."`가 스타터 코드 원문(그대로 복사),
`StaticText` 노드들을 순서대로 이으면 문제 설명 원문이다(단, 수식은
MathJax라 텍스트로 안 잡히므로 표준 브라켓 표기법으로 직접 복원해서 쓴다 —
예: "unnormalized vector |ψ̃⟩ = α|0⟩ + β|1⟩", "정규직교 기저 조건
|α|²+|β|²=1" 같은 건 Codebook 표준 표기이므로 코더사이즈 제목과 함수
docstring만 봐도 복원 가능하다).

`insane-search` 엔진(`python3 -m engine <url>`)은 이 사이트에서
`curl_cffi`/Node 의존성이 없으면 실패하고 Playwright MCP로 넘어가라고
하는데, 이 세션엔 Playwright MCP 대신 `chrome-devtools` MCP가 있으므로 위
2순위 방법을 바로 쓰면 된다.

## 2. Korean화 규칙

- **코드 블록은 원문 그대로**: docstring, 주석(`# YOUR CODE HERE` 등), 변수명,
  테스트용 `print(...)` 코드까지 전부 영어 원문 그대로 복사한다. 번역하지
  않는다 — 학생들이 실제 Codebook에서 보는 것과 동일해야 한다.
- **코드가 아닌 설명 문장은 전부 한글로** 번역한다. 공식 영어 원문에 있는
  내용만 옮기고, 없는 설명을 지어내지 않는다.
- **수식은 LaTeX**: 상태벡터·브라켓 표기(`|ψ⟩ = α|0⟩ + β|1⟩`), 정규화 조건
  (`|α|² + |β|² = 1`) 등은 마크다운 안에 인라인 `$...$` 또는 디스플레이
  `$$...$$`로 쓴다. 일반 텍스트로 풀어쓰지 않는다.

## 3. 손으로 답을 쓸 빈 칸 만들기

각 문제의 코드 블록에서 `# YOUR CODE HERE` (또는 그 아래 힌트 주석) 다음에,
**빈 줄을 5~10줄** 넣는다 — 기준은 "그 문제의 예상 정답 줄 수의 약 2배".
예:
- I.1.1(정규화, 예상 정답 ~2줄) → 빈 줄 6~8줄
- I.1.2(내적, 예상 정답 ~1줄) → 빈 줄 6~8줄 (`return` 문 앞까지, 원래 있던
  `return` 줄과 테스트용 `print` 코드는 그대로 둔다)

빈 줄은 진짜 빈 줄이지 주석(`#`)을 채우지 않는다 — 인쇄해서 학생이 그
칸에 직접 코드를 손으로 쓸 것이기 때문이다.

## 4. 파일 구조 (.md)

```markdown
# 양자 계산과학 Quiz #<N>, <월 일 년>

이름: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_       학번: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

---

## 문제 1 (Codercise <공식 번호> — <공식 제목 한글 의역>)

<한글 설명, 수식은 LaTeX>

```python
<원문 코드 그대로 + YOUR CODE HERE 아래 빈 줄 5~10개>
```

---

## 문제 2 (Codercise <공식 번호> — ...)
...
```

문제 순서 = 사용자가 지정한 순서(보통 Codebook 번호 오름차순).

## 5. 저장 위치 / 파일명

```
/Users/yongsunkim/Library/CloudStorage/GoogleDrive-kingmking@gmail.com/My Drive/개인서류 drive/수업 2026 fall 부터/수업 2026 fall/quiz/Quiz<N>_<YYYY-MM-DD>.md
```
(Google Drive가 로컬에 마운트되어 있으므로 `Write` 도구로 바로 이 경로에
쓴다 — Drive MCP `create_file`을 거칠 필요 없음.) 날짜는 사용자가 말한
시험 날짜(예: "Sept 3 2026" → `2026-09-03`)를 쓰고, 퀴즈 번호는 그 폴더에
이미 있는 `QuizN_*.md` 중 가장 큰 N 다음 번호로 정한다(사용자가 명시하지
않으면).

## 알아둘 것

- 이 스킬은 **문제만** 만든다 — 정답 채점본이 필요하면 별도로 요청받아야
  한다(이 스킬 범위 밖).
- 같은 Codercise를 나중에 실습 노트북(`pennylane-codercise-notebook`
  스킬)으로도 만들 수 있는데, 그건 정답을 채워서 실행되게 만드는 정반대
  목적이니 혼동하지 않는다.
- 코드 블록의 공백 줄 수는 인쇄 레이아웃(종이 한 장에 몇 문제가 들어가는지)
  을 고려해서 사용자가 다르게 요청하면 그에 맞춘다 — 5~10줄은 기본값이지
  고정값이 아니다.
