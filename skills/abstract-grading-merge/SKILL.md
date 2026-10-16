---
name: abstract-grading-merge
description: "학회 트랙(예: QM2027의 Small Systems 등)의 여러 채점자(POC/convener)가 각자 다른 형식의 Excel 파일로 보낸 초록(abstract) 채점 결과를 한 파일로 취합한다. 채점자마다 컬럼 구성이 다르므로(Id/Title/Score/Comment/Merge-with 등의 이름이 제각각) 헤더를 자동 인식해서 매칭하고, 사람별 0/1/2/3 점수 분포가 균등한지(목표 = 전체건수/4) 먼저 점검해서 보고한 뒤, Oral은 채점자별 점수를 평균(Average)하고 'Merge with'(병합 제안, 두 초록을 하나로 합치자는 제안) 칸은 전원 제안의 합집합으로 모으고(제안이 서로 다르면 빨간색으로 표시), Comments는 '이름: 내용' 줄 단위로 전원분을 쌓아 하나의 Comments 칸에 넣는다. Poster는 채점 데이터가 부실하면(예: 전부 똑같은 점수, 또는 대부분 미채점) 자동으로 평균표 대신 '0점 받은 것만' 플래그 목록으로 대체한다. 결과는 템플릿 파일(보통 convener가 보낸 가장 완전한 파일, Merge-with 칸이 있는 파일)의 컬럼 구조를 따르는 새 '<트랙>_merged_<날짜>.xlsx'로 저장한다(기존 파일은 절대 덮어쓰지 않음). '초록 채점 취합해줘', 'XX 트랙 점수 합쳐줘', '채점 파일들 머지해줘', 'grading 폴더에 있는거 합산해줘' 요청 시 사용. 새 채점자 파일이 추가로 들어와도(파일명이 다르고 컬럼 구성이 또 다를 수 있음) 같은 폴더에 넣고 다시 돌리면 된다 — 자동 인식이 실패하면 2절의 컬럼 별칭(alias) 목록에 새 이름을 추가한다."
---

# 초록 채점(abstract grading) 다자 취합

## 0. 배경

QM2027 같은 학회에서 트랙별 convener/POC 여러 명이 각자 독립적으로 Oral/Poster
초록에 0~3점을 매긴다. 각자 보내오는 Excel 파일의 **컬럼 이름과 구성이 전부
다르다** — 2026-10 Small Systems 트랙 기준 실제로 받은 4개 파일이 이랬다:

| 파일 | 특징 |
|---|---|
| `Small_Systems_Jacobs.xlsx` | 가장 깔끔한 템플릿. Oral: `Id,Title,Affiliation,Category,Collaboration,Score,Merge with,Comments`. Poster는 `Merge with`/`Comments` 없음. **보통 이 파일이 최종 출력의 컬럼 템플릿 역할**을 한다. |
| `17_Small_Systems_grading_AM.xlsx` | `#,Id,Title,Speaker,Authors,Type,Collaboration,Abstract,Grade,Comments` — ID는 2번째 컬럼, 점수 컬럼명은 `Grade`(`Score` 아님). Oral/Poster 둘 다 있고 Summary 탭(0/1/2/3 균등성 자체 계산)도 포함. |
| `17_Small_Systems_NagleScores.xlsx` | `Abstract #,Title,Collaboration,Score,Note` — comment 컬럼명이 `Note`. Merge 제안이 `Note`에 자유 텍스트로 (`"merge w/ 1031"`) 들어있다. |
| `17_Small_Systems_YL.xlsx` | **Indico 원본 export를 그대로 재활용** — 34개 컬럼짜리 raw export에 `Score` 컬럼만 수동으로 채워 넣은 형태. `Score` 바로 다음, `Score standard deviation` 바로 전에 **헤더 없는(None) 자유노트 컬럼**이 하나 끼어있는 게 특징(예: 리뷰어가 "IS", "Potential conflict of interest..." 같은 메모를 씀). Poster 탭은 거의 비어있었음(22건 중 1건만 채점 — 사실상 미채점). |

**핵심 교훈**: 매번 새 채점자 파일이 들어올 때마다 컬럼 이름이 또 다를 수
있다. 그래서 이 스킬은 헤더 이름을 유연하게(대소문자 무시, 동의어 목록으로)
매칭하고, 매칭에 실패하면 조용히 그 파일을 건너뛰지 않고 어떤 파일의 어떤
컬럼을 못 찾았는지 티가 나게 만든다 (해당 리뷰어의 점수/코멘트가 전부 비어
있는 이상한 결과로 나타남 — 그러면 2절의 별칭 목록을 보강한다).

## 1. 실행

```bash
python3 scripts/merge_grades.py "<폴더 경로>" [--track <트랙 토큰>] [--out <출력 경로>]
```

- `<폴더 경로>`: 채점자들의 .xlsx 파일이 모여있는 폴더. `~$...xlsx`(Excel 잠금
  파일), 이미 만들어진 `*_merged_<8자리날짜>.xlsx` 출력물은 자동으로 무시한다.
- `--track`: 리뷰어 이름을 추측할 때 파일명에서 떼어낼 토큰(예:
  `Small_Systems`). 생략하면 파일명들의 공통 접두어로 자동 추론한다 — 추론이
  이상하면 명시적으로 넘겨준다.
- `--out`: 생략하면 `<폴더>/<트랙>_merged_<YYYYMMDD>.xlsx`로 저장한다.
  **기존 스냅샷은 절대 덮어쓰지 않음** — 같은 날 두 번 돌리면 `_2`가 붙는다.
  (사용자가 재취합을 요청할 때마다 새 타임스탬프 파일로 — 과거 비교를 위해
  이전 파일은 보존.)

실행하면 터미널에 **채점자별 0/1/2/3 분포(균등성 체크)**가 먼저 출력된다 —
이걸 사용자에게 꼭 요약해서 보여줄 것 (1절 핵심 요청사항). 목표는
`전체 채점건수 / 4`이고, 모든 등급의 편차가 `max(2, 목표*0.25)` 이내면 `OK`,
아니면 `UNEVEN`으로 표시된다. 이 표는 출력 파일의 `Evenness check` 탭에도
그대로 남는다.

## 2. 컬럼 자동 인식 (별칭 목록)

`scripts/merge_grades.py`의 `*_ALIASES` 집합이 헤더 이름을 역할별로 매칭한다
(대소문자 무시):

- ID: `id`, `abstract #`, `abstract id`, `#id`, `abstract`
- Title: `title`
- Affiliation: `affiliation`
- Category: `category`, `type`
- Collaboration: `collaboration`, `if yes, please enter the collaboration name.`
- Score: `score`, `grade`
- Comment: `comments`, `comment`, `note`, `notes`
- Merge-with (명시적 숫자 칸): `merge with`

새로 들어온 파일이 이 중 어디에도 안 걸리는 이름을 쓰면(예: `평가` 같은
한글 헤더, `Rating` 등) 위 집합에 그 문자열을 추가한다. **ID 컬럼이
안 잡히면 그 파일 전체가 조용히 스킵되니**, 실행 후 터미널에 찍히는
"Reviewer files detected" 목록에 그 파일이 빠져 있는지, 또 Evenness
check에 그 리뷰어 줄이 있는지로 확인한다.

**Merge-with 제안은 명시적 컬럼 없이 Comment 안에 자유 텍스트로도 온다**
(`"merge with 596"`, `"merge w/ 1031"`, `"Merge 684"` 등). 정규식
`MERGE_PAT`가 `merge (with|w/)? #?숫자` 패턴, 그리고 `"A or B"`/`"A, B"` 식
복수 제안까지 잡아낸다. 새로운 표현(예: `"should be combined with 123"`)이
나오면 이 정규식을 넓힌다.

**헤더 없는 자유노트 컬럼** (YL 파일처럼 Indico raw export를 재활용한 경우):
`Score` 바로 다음 칸이 비어있는 헤더인데 그 다음다음 칸이 `Score standard
deviation`이면, 그 빈 칸을 comment 소스로 쓴다. Indico export를 그대로
재활용하는 채점자가 또 나오면 이 특수 케이스를 참고.

## 3. 합산 규칙 (2026-10 QM2027 Small Systems에서 확정된 방식)

- **Oral**: 점수는 **평균(AVERAGE)** — 합계(SUM)가 아니다. 사용자가 명시적으로
  "평균만"이라고 확정함 (처음엔 "점수를 합쳐"라고 했어서 합계로 오해하기
  쉬운데, 실제로는 평균 한 컬럼만 원함). 출력 시트에는 채점자별 원점수 컬럼을
  전부 남기고 `Average` 칸은 **엑셀 수식** `=AVERAGE(각 채점자 칸 범위)`로
  넣는다(값을 미리 계산해서 박아넣지 않음 — 나중에 채점자 칸을 고치면 자동
  재계산되게). 결측(아직 안 채점한 사람)은 AVERAGE가 자동으로 무시하니 손댈
  필요 없음.
- **Merge with**: 전원의 제안을 **합집합**으로 모아서 쉼표로 나열. 서로 다른
  초록을 가리키면(예: 한 명은 "208과 합치자", 다른 명은 "209와 합치자") 그
  칸을 빨간 글씨로 표시하고 Comments 맨 앞에 "제안이 다르다" 경고를 자동으로
  붙인다 — 실제로 합칠지는 convener 회의에서 결정할 문제라 자동으로 하나를
  고르지 않는다.
- **Comments**: 채점자별로 `이름: 내용` 한 줄씩, 코멘트를 남긴 사람만. 순서는
  `merge_grades.py`가 파일을 읽은 순서(보통 파일명 알파벳 순) — 특정 순서가
  중요하면 호출 전에 폴더 안 파일명을 조정하거나 스크립트의 딕셔너리 순서를
  바꾼다.
- **Poster**: 실제로는 흔히 "아직 다들 제대로 채점을 안 한 상태"다. 아래
  기준(둘 다 만족)을 못 넘는 채점자는 "진짜 채점"으로 안 치고, 그런 채점자가
  2명 미만이면 평균표 대신 **0점만 뽑은 플래그 목록**(`Poster_zero_flags`
  탭)으로 대체한다:
  1. 전체 Poster 건수의 80% 이상을 채점했는가 (너무 적으면 사실상 미채점)
  2. 채점한 값이 전부 똑같지 않은가 (전부 "1점" 같은 건 placeholder로 간주)

  2026-10 사례: Jacobs는 22건 전부 1점(placeholder), AM은 0건, YL은 1/22건
  뿐이라 셋 다 "진짜 채점"에서 빠지고 Nagle(22/22, 분포도 6/6/5/5로 정상)만
  남아 1명 — 기준(2명 이상) 미달이라 평균표 대신 Nagle이 0점을 준 5건만
  플래그 리스트로 남겼다. **나중에 더 많은 채점자가 Poster를 채점하면 이
  기준을 자동으로 넘기고 Oral처럼 평균표가 나온다** — 코드를 안 고쳐도 됨.

이 "Poster는 데이터 부실하면 자동으로 skip" 판단은 2026-10 Small Systems
트랙 상황(사용자가 "poster는 무시해라!!"라고 명시적으로 확정)에서 나온
휴리스틱이다. 다른 트랙에서 Poster가 실제로 멀쩡히 다 채점되어 있으면
자동으로 평균표가 나오니 걱정 없지만, 애매한 경계 상황이면 사용자에게
먼저 분포를 보여주고 확인받는 게 안전하다(실제로 2026-10 세션에서도 먼저
분포표를 보여주고 사용자 확인을 받은 뒤 진행했다).

## 4. 리뷰어 이름 추측

파일명에서 `--track` 토큰과 `grading/scores/score/grades/grade` 같은 흔한
접미어, 그리고 선행 숫자(트랙 번호 접두어, 예: `17_`)를 떼어낸 나머지를
리뷰어 이름으로 쓴다 (`guess_label()`). 예:
- `17_Small_Systems_grading_AM.xlsx` → `AM`
- `17_Small_Systems_NagleScores.xlsx` → `Nagle`
- `Small_Systems_Jacobs.xlsx` → `Jacobs`

새 파일 이름이 이 규칙으로 이상하게 추측되면(예: 전체 파일명이 그대로
나옴) `--track`을 더 구체적으로 주거나, 터미널에 찍히는 "Reviewer files
detected" 목록을 보고 바로 알 수 있다 — 사용자에게 보여주고 이름이
맞는지 확인.

## 5. 출력 포맷 확인 (openpyxl + 수식)

- 전 영역 Arial 폰트, 헤더는 옅은 파란 배경(`DDEBF7`) + 볼드.
- `Average` 컬럼은 실제 수식 — `xlsx` 스킬 규칙상 **LibreOffice(`soffice`)로
  recalc.py를 돌려 수식 에러가 없는지 확인**해야 하는데, 이 Mac에는
  LibreOffice가 없을 수 있다(2026-10 세션에서 없었음). 그 경우 수식 문자열이
  올바른 범위를 가리키는지(`get_column_letter` 계산) 직접 확인하고, 사용자가
  실제 Excel로 열면 정상적으로 계산된다는 점을 알려준다. LibreOffice가 있는
  컴퓨터라면 꼭 `recalc.py`로 검증할 것.
- 매 실행마다 Oral(있으면), Poster 또는 Poster_zero_flags(상황에 따라),
  Evenness check 세 탭을 만든다.
