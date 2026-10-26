---
name: qm2027-selection-stats
description: "QM2027 'POC's parallel selection' Google Sheet(17개 트랙 탭)의 Primary list(90%, 승인된 구두발표)를 모아 Theory/Experiment 갯수, collaboration(ALICE/ATLAS/CMS/STAR/sPHENIX 등)별 발표 갯수, 발표자 남녀 비율 통계를 낸다. 트랙별 시트의 'Affiliation' 칸은 트랙마다 기관명일 때도, 발표자 이름일 때도 있어 신뢰할 수 없으므로 Category/Collaboration/Presenter는 항상 최신 Indico abstract book PDF(/Users/yongsunkim/My Gdrive/개인서류 drive/QM2027/QM2027_abstracts_all_<날짜>.pdf, 없으면 Indico에서 새로 받음 — qm2027-plenary-recommendation 스킬 패턴 참고)에서 가져온다. CMS/STAR/ATLAS/sPHENIX 같은 대형 collaboration은 Indico 제출 규정상 한 사람(컨비너) 이름이 수십 개 talk의 '발표자' 란에 placeholder로 반복되므로(실제 발표자는 TBD), 이런 talk는 성비 집계에서 자동 제외한다(scripts/aggregate_stats.py의 LIAISON_TRACK_THRESHOLD 휴리스틱). 결과는 사용자가 'html로 해' 라고 하면 Artifact Dashboard 타입으로 publish한다. '전체 트랙 합쳐서 통계 내줘', '몇 명이 여자/남자야', 'collaboration별로 몇 개야', 'theory experiment 비율' 요청 시 사용. 트랙 하나만 요청하면(예: 'EM만') 그 트랙의 Primary list만 돌린다 — 전체 요청('전체를 합쳐서', '트랙별로 나눌 필요 없다')과 구분할 것."
---

# QM2027 parallel-talk selection 통계

## 0. 언제 쓰나

사용자가 QM2027 "POC's parallel selection" Google Sheet
(`https://docs.google.com/spreadsheets/d/1ZqmpO3KbaSxb8vlC7ihNtM4TGSkmO3-IxgQ-WeHrves`)
에 모인 구두발표 선정 결과를 가지고 Theory/Experiment 비율, collaboration별
발표 수, 발표자 성비 같은 통계를 요청할 때 쓴다. 범위는 매번 다를 수 있다 —
트랙 하나만(예: "EM 트랙 통계 내봐")일 수도, 채워진 트랙 전체를 합친
것("전체를 합쳐서", "트랙별로 나눌 필요 없다")일 수도 있다. 사용자의 scope
지정을 우선하고, 명시가 없으면 **Primary list(90% 승인 리스트)만** — Secondary
candidate는 2nd round에서 트랙이 바뀔 수 있는 미확정 리스트이므로 기본적으로
제외한다.

이 시트와 Poster-무시 규칙에 대한 배경은 세션 메모리의
`project_qm2027_poc_tracking.md`를 참고(있다면). 이 스킬 자체는 그 메모와
별개로, "통계를 어떻게 정확하게 뽑는가"에 대한 절차다.

## 1. 트랙별 채움 상태 확인 + Primary list ID 수집 (Google Sheet)

1. 시트를 열고(브라우저 자동화 — `claude-in-chrome` 스킬 참고. 로그인된
   브라우저가 여러 개 연결돼 있으면 반드시 사용자에게 물어서 선택한다) 각
   트랙 탭(`CH, CD, EM, FA, EI, LC, AQ, HF, IS, JE, LF, NT, AS, UP, CP, SM,
   EX`)을 돈다.
2. 채움 여부는 `B6`(Primary list 첫 데이터 행의 Id 칸)이 비어있는지로
   빠르게 판단한다. 비어있으면 그 트랙은 아직 POC 결과가 안 들어온 것 —
   통계에서 제외하고, 필요하면 Row 1의 POC Liaison 이름을 사용자에게 알려준다.
3. 채워진 트랙은 Row 4 라벨("Oral — Primary list (90% target: N talks)")로
   Primary 블록의 행 범위를 확인하고, `A4:F<끝행>` 범위를 Name Box로 선택해
   스크린샷/zoom으로 **Id, Category, Collaboration** 열을 읽는다. 이 두 열은
   트랙 시트 안에서는 꽤 정확한 편이라 PDF 없이도 쓸 수 있지만, 사람이 보고
   읽은 것이므로 숫자가 많은 트랙(20개 이상)은 아래 2절의 PDF 교차검증으로
   덮어쓰는 걸 권장한다. **Affiliation 열은 쓰지 않는다** — 트랙마다 기관명
   (EM, IS 등)과 발표자 이름(CD, LC 등)이 섞여 있어 신뢰할 수 없다.
4. UP 트랙처럼 Primary/Secondary 구분이 없고 "Accepted (N talks, no
   ranking)" 식으로만 돼 있는 트랙은 그 Accepted 블록 전체(및 TOP/must-include
   행이 따로 있으면 그것도)를 Primary로 취급한다.
5. 각 트랙의 Primary ID 리스트를 `{"CD": [183, 488, ...], "EM": [630, ...],
   ...}` 형태의 JSON으로 정리한다(스크래치패드에 `tracks.json`으로 저장).

## 2. Indico abstract book PDF에서 Category/Collaboration/Presenter 가져오기

시트의 Category/Collaboration은 신뢰할 수 있지만 **발표자 이름(성비 집계에
필요)은 시트에 아예 없다** — Affiliation 칸이 이름인 트랙도 있지만 일관되지
않으므로, Category/Collaboration/Presenter 세 개 다 PDF에서 한 번에 뽑는 게
가장 안전하고 빠르다.

1. `/Users/yongsunkim/My Gdrive/개인서류 drive/QM2027/`에 날짜가 가장 최근인
   `QM2027_abstracts_all_<날짜>.pdf`가 있는지 먼저 확인한다(`mdfind`나
   Finder로 — `~/Downloads`와 달리 이 경로는 보통 샌드박스 제약이 없다).
   오늘 날짜 기준 PDF가 없거나 너무 오래됐으면(며칠 이상) Indico에서 새로
   받는다: `indico.cern.ch/event/1622375/manage/abstracts/list/` (CERN SSO
   로그인은 사용자가 직접 — 절대 대신 로그인하지 않는다) → 전체 선택(All) →
   Export → PDF. **Chrome이 PDF를 내장 뷰어로 열어버려 자동화로 다운로드
   버튼을 못 누르는 경우가 많다** — 그럴 땐 일반 페이지(목록 페이지)로
   돌아가서 `javascript_tool`로 같은 URL을 `fetch(..., {credentials:
   'include'})`한 뒤 blob을 만들어 `<a download>`로 저장하면 된다(세션
   쿠키를 그대로 쓰므로 인증 문제 없음). 받은 파일은 Downloads에 떨어지는데
   그것도 샌드박스로 못 읽을 수 있으니, 사용자에게 Drive 폴더로 옮겨달라고
   하거나 Finder(`osascript`)로 복사해서 스크래치패드로 가져온다.
2. `pdftotext -layout QM2027_abstracts_all_<날짜>.pdf all.txt`
3. `python3 scripts/extract_abstracts.py all.txt all_abstracts.json` —
   모든(1000개 이상) abstract의 Category/Collaboration/Affiliation/Presenter/
   Author를 파싱해 ID별 JSON으로 저장한다. 페이지 넘김 때문에 필드 값에
   `\n`과 "Quark Matter 2027 / Report of Abstracts" 같은 머리글이 섞여
   들어오는데, 이는 다음 단계(`aggregate_stats.py`의 `clean()`)에서 정리한다.

## 3. 집계

```bash
python3 scripts/aggregate_stats.py tracks.json all_abstracts.json
```

이 스크립트는:
- **Theory/Experiment 총계**와 **collaboration별 발표 수**(Experiment만,
  collaboration 이름은 "STAR Collaboration" → "STAR" 식으로 정규화)를
  표준출력에 찍는다.
- 발표자 이름이 **collaboration 자체("ALICE", "ALICE COLLABORATION" 등)**이거나,
  **같은 이름이 4개 이상 서로 다른 트랙에 반복 등장**하면(대형 collaboration의
  컨비너가 "Indico가 발표자 입력을 요구해서" 자기 이름을 placeholder로 쓴
  경우 — 실제 QM2027에서 McGinn(CMS), Leung(STAR), Rosati(sPHENIX),
  Steinberg(ATLAS) 같은 이름이 10개 이상 트랙에 걸쳐 나타났다) **성비 집계
  대상에서 자동 제외**하고 `excluded_presenters.json`에 이유와 함께 남긴다.
  이 휴리스틱이 틀릴 수 있으니(진짜로 한 사람이 여러 개 제출했을 수도 있음)
  제외 목록을 한 번 훑어서 말이 되는지 확인한다.
- 나머지(진짜 개인 제출로 보이는 talk)는 `individual_presenters.json`에
  담겨 사람이(또는 Claude가) 성별을 매기도록 넘겨준다.

**성별 매핑은 스크립트에 하드코딩하지 않는다** — 매번 발표자 명단이 다르므로,
`individual_presenters.json`을 열어 각 `presenter`의 이름(앞쪽 given name
기준)으로 성별을 판단한다. 확실한 경우만 Male/Female로 표시하고, 성별이
불분명한 이름(많은 동아시아권 이름, 유니섹스 이름 등)은 **추측하지 말고
Unknown으로 남긴다** — 틀린 추측이 맞는 추측보다 훨씬 나쁘다. "Ms"/"Dr"/
"Prof." 같은 호칭 자체에 성별 정보가 있는 경우(Ms, Mr)는 그대로 활용.

## 4. 출력

사용자가 "html로 해"라고 하면 Artifact 도구로 **Dashboard 타입**(quickstart
intent "other" → Dashboard type_url)에서 시작한다. 데이터가 커넥터가 아니라
이렇게 수작업으로 모은 값이므로 `datasets/<id>`의 `source`는
`{kind: "file", ...}`로 CSV를 업로드해 붙인다(라이브 쿼리 아님, `fixed:
true`). 최소한 다음 세 그림은 넣는다: Theory/Experiment 막대, collaboration별
막대, 성비 막대(+ "제외된 placeholder N건" 각주). Artifact 도구 자체의
Dashboard 타입 지침(quickstart 결과로 받는 것)을 그대로 따른다 — 이 스킬은
데이터 준비까지만 담당.

HTML을 요청하지 않았으면 그냥 채팅에 숫자로 요약해서 답한다.

## 5. 재실행 시 유의

- 트랙이 새로 채워지거나(POC 결과 추가 도착) PDF가 갱신되면 1절부터 다시
  돈다 — 이전 `tracks.json`/`all_abstracts.json`을 재사용하지 말고 새로
  받는다(Indico 초록 ID가 바뀌진 않지만 트랙 재배정이 있을 수 있음).
- Secondary candidate까지 포함해서 통계를 내 달라고 하면 1절에서 Secondary
  블록의 ID도 같이 모으고, 집계 결과에서 "Primary만"이 아니라 "Primary +
  Secondary"임을 명시한다 — 둘을 섞어서 보고하지 않는다.
