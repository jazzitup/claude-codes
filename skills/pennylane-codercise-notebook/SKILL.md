---
name: pennylane-codercise-notebook
description: >
  Build one standalone, actually-runnable Google Colab notebook that covers
  every PennyLane Codebook codercise for a given course week (e.g. "Week1 -
  codercise I.1.1 - I.3.1.ipynb"), and drop it into the class's Google Drive
  exercise-code folder. PennyLane Codebook codercises are code *fragments*
  ("YOUR CODE HERE" stubs) that don't run on their own — this skill fills
  each one in, adds print statements so students can see values change,
  draws circuit diagrams for anything QNode-based, verifies every cell
  actually executes with no errors, and packages the whole week into a
  single notebook with a markdown title + Codebook link before each
  exercise. Use when the user asks to make "week N codercise 실습 노트북" /
  "standalone 코더사이즈 노트북" / extend last week's exercise-code notebook to
  the next module, for the "quantum_computing_class" course (Sejong
  University, Prof. Yongsun Kim). Korean triggers: 코더사이즈 노트북 만들어줘,
  week2/3 실습코드, 코드북 연습문제 standalone으로.
---

# PennyLane Codercise → Standalone Week Notebook

이 스킬은 2026-08-31에 Week 1 (`Codebook I.1.1 ~ I.3.1`)을 만들면서 확립한
과정을 그대로 재사용해서, 다음 주차 노트북(Week2, Week3, ...)을 같은 품질과
같은 스타일로 만든다. 실제로 만들어본 파일:
`Week1 - codercise I.1.1 - I.3.1.ipynb` (Google Drive
[실습코드 폴더](https://drive.google.com/drive/folders/1JOz5Xw07RXiW9WMbRB4LEtREqoezS2OK)).

## 0. 이번 주차가 어떤 Codebook 모듈을 다루는지 확정한다

기준 문서: 강의 디렉토리의
`Yongsun Kim - Introduction to Quantum Computing - Xanadu recommended resources.pdf`
(Read 도구로 직접 읽는다). 이 PDF의 "Module N – ..." 섹션마다 그 주차가
다루는 "Codebook Module X.Y" 목록이 나열되어 있다.

이 강의는 **Week 번호 = 이 PDF의 Module 번호**로 이미 일대일 대응되어 있다
(강의 디렉토리의 기존 파일명, 예: `Week02_Module2_single_qubit_gates_보강판.md`,
`Week07_ModulePF_pennylane_fundamentals_보강판.md`로 확인됨). 2026-08-31 기준
확인된 매핑:

| Week | PDF Module | Codebook 모듈 | 주제 |
|---|---|---|---|
| 1 | Module 1 | I.1, I.2, I.3 | 큐비트/서킷/유니터리 |
| 2 | Module 2 | I.4, I.5, I.6, I.7 | 1-큐비트 게이트, 위상, 회전게이트, Bloch sphere |
| 3 | Module 3 | I.8, I.9, I.10 | 상태 준비, 사영측정, 기댓값 |
| 4 | Module 4 | I.11, I.12, I.13, I.14 | 텐서곱, 얽힘, CZ/Toffoli/SWAP, Bell |
| 5 | Module 5 | A.1, A.2, A.3 (+teleportation demo) | 지수적 속도향상, oracle |
| 6 | Module 6 | A.4, A.5, A.6 | Deutsch-Jozsa |
| 7 | Module PF | PF.1~PF.6 | PennyLane Fundamentals |
| 8 | Module G1 | G.1, G.2, G.3 | Grover part 1 |
| 9 | Module G2 | G.4, G.5 | Grover part 2 |
| 10 | Module F | F.1, F.2, F.3 | QFT |
| 11 | Module P | P.1~P.4 | QPE |
| 12 | Module S1 | S.1, S.2, S.3 | Shor part 1 |

(Module S2/N1/N2/D/E1/E2/H1/H2는 이 강의 디렉토리에 아직 WeekNN 파일이 없다 —
실제로 요청받으면 PDF에서 Module 번호를 다시 확인할 것. 이 표는 참고용
캐시일 뿐, PDF가 실제 소스다.)

**사용자가 "Week N 만들어줘"라고만 말하면 이 표로 Codebook Module 목록을
확정**하고, 애매하면 PDF를 다시 읽어 확인한다. 각 "Codebook Module X.Y"
안에 속한 하위 코더사이즈는 X.Y.1, X.Y.2, ... 전부이며(마지막 모듈만 사용자가
범위를 잘라달라고 하는 경우가 있음 — Week1은 I.3의 코더사이즈가 2개였는데
I.3.1까지만 요청받았다), 명시적으로 다르게 말하지 않으면 **그 모듈의
코더사이즈를 전부** 포함한다.

## 1. 각 모듈의 공식 코더사이즈 목록 + 문제원문 + 코드 템플릿을 가져온다

**우선순위 1순위: `pennylane-codebook-notes` 스킬의 추출 스크립트를 그대로
재사용한다.** PennyLane Codebook은 Next.js 사이트라 WebFetch로는 빈 제목만
나온다(SPA라서). 대신 서버가 최초 HTML 응답에 박아 넣는 Next.js RSC 스트림을
직접 파싱하면 `exercises` 배열(공식 문제 원문 + `codeTemplate`)을 그대로 얻을
수 있다 — 이미 검증된 방법이다 (2026-08-31, I.1 페이지에서 5개 코더사이즈
전부 정확히 추출 확인함).

```bash
mkdir -p <workdir>
source ~/.claude/skills/pennylane-codebook-notes/scripts/setup_env.sh <workdir>
source <workdir>/venv/bin/activate
python3 ~/.claude/skills/pennylane-codebook-notes/scripts/extract_theory.py \
  "<codebook 모듈 URL>" "<workdir>/<slug>.json"
```

결과 JSON의 `exercises` 배열 원소마다:
- `slug` — 코더사이즈 슬러그 (예: `01-normalization-of-quantum-states`)
- `title` — 공식 제목 (예: "Codercise I.1.1 — Normalization of quantum states") **이 공식 제목을 그대로 마크다운 헤더에 쓴다** — 직접 지어내지 말 것.
- `content` — 문제 원문 (마크다운, LaTeX 포함) — 한국어 요약을 쓸 때 이 원문에
  없는 내용을 지어내지 않는다.
- `codeTemplate` — `# YOUR CODE HERE` 스텁이 있는 미완성 코드. **이걸 완성해서
  실행 가능하게 만드는 것이 이 스킬의 핵심 작업이다.**

각 URL의 정확한 슬러그(예: `all-about-qubits`, `quantum-circuits`,
`unitary-matrices`)는 코드북 URL을 짐작하지 말고 `WebSearch`로
`pennylane.ai codebook <주제>` 검색해서 검색결과 링크에서 정확한 URL을 확인한다
(2026-08-31에 확인된 I.1~I.3 URL):
- I.1: `https://pennylane.ai/codebook/introduction-to-quantum-computing/all-about-qubits`
- I.2: `https://pennylane.ai/codebook/introduction-to-quantum-computing/quantum-circuits`
- I.3: `https://pennylane.ai/codebook/introduction-to-quantum-computing/unitary-matrices`

**우선순위 2순위 (교차검증용): 커뮤니티 솔루션 저장소.** GitHub의
`ashmitjsg/Xanadu-Codebook-Solutions` (2022년 당시 `devilkiller-ag` 계정으로
만들어졌다가 이후 원 작성자 계정으로 옮겨짐 — repo가 이동한 경우
`https://api.github.com/repos/<old_owner>/<repo>`가 301을 반환하니
`url`/`full_name` 필드로 새 위치를 따라가야 한다)의 `solutions/` 아래에
`I1-01-....ipynb`, `I2-03-....ipynb`처럼 `<모듈번호><코더사이즈번호>-<이름>.ipynb`
형식으로 I.1~I.4 코더사이즈 풀이가 있다. 원문 raw 코드는
`https://raw.githubusercontent.com/<owner>/<repo>/<branch>/solutions/<file>.ipynb`.

⚠️ **이 저장소 풀이를 그대로 베끼지 말 것 — 실제로 버그를 발견했다**
(2026-08-31, I.1.5: `apply_u(state)`의 반환값을 `state`에 재대입하지 않아서
측정 단계가 U 적용 전 상태를 측정하던 문제; `qml.prob`처럼 실제로는
존재하지 않는 함수명을 쓴 셀도 있었다 — 맞는 이름은 `qml.probs`). 참고
자료로만 쓰고, 최종 코드는 **반드시 2단계(직접 실행 검증)를 통과한 것만**
채택한다.

## 2. 각 코더사이즈를 "눈으로 확인 가능한" 완성 코드로 만든다

`codeTemplate`의 `# YOUR CODE HERE` 부분을 채워서 완성하되, 그대로 두지 않고
다음을 항상 추가한다 (Week1에서 세운 스타일):

- 함수를 정의한 뒤 **의미 있는 입력값으로 실제 호출**하고, 결과를 `print(f"...")`
  로 라벨 붙여 출력한다. 코더사이즈 채점기가 요구하는 최소 코드가 아니라,
  "이게 왜 맞는지" 학생이 값으로 확인할 수 있게 하는 게 목적이다.
- 확률 계산은 항상 `np.abs(x) ** 2`를 쓴다 (`np.square(x)`는 복소수에서
  `|x|^2`이 아니라 `x^2`을 계산하므로 버그가 된다 — 커뮤니티 저장소에서
  실제로 이 실수를 봤다).
- 검증 가능한 주장(정규화 조건, 두 방식이 같은 결과를 내야 한다는 것 등)은
  `np.allclose(...)`나 직접 계산한 값으로 `print`해서 참/거짓을 보여준다.
- QNode/회로가 있는 코더사이즈는 실행 후 반드시
  `fig, ax = qml.draw_mpl(circuit)(...); plt.show()`로 회로 그림을 그린다.
  (ASCII `qml.draw`가 아니라 `draw_mpl`을 쓴다 — "그림"을 요청받았을 때는
  실제 이미지가 나와야 한다.)
- 흔한 실수(예: 함수 반환값을 재대입하지 않음)가 있는 문제라면, 그 부분을
  주석으로 짚어준다 — Week1의 I.1.5가 그런 사례였다.

## 3. 노트북 하나로 합친다 (마크다운 제목 + 링크 + 코드)

Week1의 `<workdir>/build_notebook.py` 방식을 그대로 따른다:
nbformat 4 JSON을 `json.dump`로 직접 만드는 파이썬 스크립트를 짜서
(python 라이브러리로 노트북을 조작하지 말고 dict/JSON을 직접 구성하는 게
가장 사고가 적다), 다음 순서로 셀을 쌓는다.

1. 전체 제목 마크다운 (`# Week N — PennyLane Codercise 실습 (Codebook ...)`) —
   "코더사이즈는 코드 조각이라 그대로 안 돌아간다"는 설명 1회.
2. `## 0. PennyLane 설치` 마크다운 + `!pip install pennylane` 코드 셀.
3. 모듈별로: `## Codebook X.Y — <모듈 제목>` 마크다운(그 모듈 페이지 링크 포함,
   맨 처음 그 모듈이 등장할 때 1회) → 코더사이즈마다
   `### Codercise X.Y.Z — <공식 제목>` 마크다운(짧은 설명 + 같은 모듈 링크
   재게시) → 완성된 코드 셀 1개(또는 draw_mpl까지 포함해 필요하면 여러 개).
4. 맨 끝에 `## 요약` 마크다운으로 이번 주 모듈들을 1줄씩 정리하고, 다음 주
   예고를 한 줄 넣는다(PDF의 다음 Module 제목을 참조).

파일명 규칙: `Week<N> - codercise <첫코더사이즈번호> - <마지막코더사이즈번호>.ipynb`
(Week1 예: `Week1 - codercise I.1.1 - I.3.1.ipynb`). **로마자 대문자 `I`를 쓴다**
(소문자 `l`이 아니다) — Codebook 공식 표기가 `I.1.1`이기 때문이다.

## 4. 실행 검증 — 반드시 통과할 것

절대로 안 돌려보고 올리지 않는다. 이 스킬의 헬퍼 스크립트를 쓴다:

```bash
bash ~/.claude/skills/pennylane-codercise-notebook/scripts/verify_notebook.sh \
  <workdir> "<workdir>/Week<N> - codercise ... .ipynb"
```

이 스크립트는 `<workdir>/venv`에 Colab이 실제로 까는 PennyLane 버전(pip가
주는 최신 안정판, 2026-08-31 기준 0.45.1)을 설치하고, `jupyter nbconvert
--execute`로 노트북을 처음부터 끝까지 실제 실행한 뒤, 에러가 하나라도 있는
셀이 있으면 논제로 종료코드로 실패한다. **에러 없이 통과할 때까지 코드를
고친다.** 통과 후 `<workdir>/<이름>.executed.ipynb`의 스트림 출력을 한 번씩
훑어서 숫자가 말이 되는지(확률 합이 1인지, 두 방식이 같은 결과를 내는지 등)
확인한다 — 에러 없음 ≠ 값이 맞음.

## 5. Google Drive 실습코드 폴더에 저장한다

⚠️ **`create_file`(Google Drive MCP)의 `base64Content`에 큰 텍스트를 손으로
옮겨 붙이지 말 것.** 2026-08-31에 18KB짜리 노트북을 base64로 옮기다가 중간에
공백 한 글자가 섞여 "not a valid base64 string" 에러가 났다. 대신 이
사용자의 Google Drive는 Google Drive 데스크톱 앱으로 로컬에 마운트되어
있으므로, 그냥 파일시스템에 직접 쓴다:

```bash
cp "<workdir>/Week<N> - codercise ... .ipynb" \
  "/Users/yongsunkim/Library/CloudStorage/GoogleDrive-kingmking@gmail.com/My Drive/Colab Notebooks/quantum computational sceince 2026 fall/"
```

경로가 바뀌었을 수 있으니, 먼저 `find "/Users/yongsunkim/Library/CloudStorage/GoogleDrive-kingmking@gmail.com" -iname "*codercise*"`로 기존 Week1 파일 위치를
확인해서 같은 폴더에 넣는다. 복사 후 몇 초~수십 초 뒤 Google Drive MCP의
`search_files`(`parentId = '1JOz5Xw07RXiW9WMbRB4LEtREqoezS2OK'`)로 클라우드에
실제로 올라갔는지(파일 크기가 로컬과 같은지) 확인한다.

기존 주차 파일을 다시 만들어 교체하는 경우(같은 주차를 다시 요청받은 경우)에만,
Drive MCP의 `trash_file`로 옛 파일을 휴지통으로 보낸다 — Drive API는 파일
내용을 그 자리에서 바꾸는 기능이 없으므로, 항상 "새로 만들고 옛것은 휴지통"
방식이다. `update_file`은 제목/부모 폴더만 바꿀 수 있고 내용은 못 바꾼다.
새 주차(예: Week2)를 처음 만드는 경우는 옛 파일이 없으니 trash 단계 자체가
없다.

## 알아둘 것 (2026-08-31에 겪은 함정들)

- `pennylane.ai/*` 페이지는 WebFetch로 못 읽는다(SPA라 제목만 나옴) —
  `WebSearch`로 정확한 URL을 찾고, 페이지 본문은 `extract_theory.py`로
  가져온다(위 1단계).
- `qml.specs(circuit)(*args)`가 반환하는 객체는 `.depth`가 바로 있는 게
  아니라 `.resources.depth`에 있다 (PennyLane 0.45.1 기준, 회로 깊이 관련
  코더사이즈에서 필요할 수 있음).
- GitHub 저장소가 이동(rename/transfer)된 경우 `api.github.com/repos/<owner>/<repo>/...`가 301을 반환한다 — 응답의 `url`(저장소 id 기반 API URL)을
  따라가서 실제 `full_name`을 확인한 뒤 `raw.githubusercontent.com/<새 owner>/...`
  로 다시 받는다.
- 큰 텍스트(노트북 JSON 등)를 Drive MCP에 base64로 손 옮겨적지 말 것(위 5단계
  참고) — 로컬 마운트 경로에 직접 쓰는 게 훨씬 안전하다.
- 완성 코드는 community 저장소를 그대로 신뢰하지 말고 항상 4단계 실행
  검증을 통과한 버전만 최종 채택한다.
