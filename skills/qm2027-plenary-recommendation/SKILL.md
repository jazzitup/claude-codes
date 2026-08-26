---
name: qm2027-plenary-recommendation
description: "최근 N일(기본 10일)간의 Gmail을 뒤져 QM2027 Plenary/Lecturer 추천 이메일(직접 kimy@cern.ch·kingmking@gmail.com으로 오거나, secretariat@qm2027.kr가 qm2027_coloc@googlegroups.com으로 forward한 것)을 찾아, Google Drive의 'QM2027_IAC_Recommendation for plenary.xlsx' 템플렛에 채워 넣고 파일명에 날짜/시간을 붙여 새 파일로 저장한다. 'QM2027 추천 정리해줘', 'IAC 추천 엑셀 채워줘', '플레너리 추천 취합해줘' 요청 시 사용."
---

# QM2027 IAC Plenary/Lecturer 추천 취합

## 0. 배경

QM2027 (Quark Matter 2027) 학술대회의 IAC(International Advisory Committee)
위원들이 Plenary 강연자와 Student (Junior) Day Lecturer 후보를 이메일로 추천해
온다. 이 추천들은 두 경로로 들어온다:

1. IAC 위원이 `secretariat@qm2027.kr`로 보내면, 사무국이 그걸 그대로
   `qm2027_coloc@googlegroups.com` (Co-LOC 그룹, kingmking@gmail.com 포함)으로
   `FW:` 제목을 달아 전달한다.
2. IAC 위원이 김용선 교수 개인 메일(`kimy@cern.ch` 또는 `kingmking@gmail.com`)로
   직접 답장하는 경우도 있다.

사용자(김용선 교수)는 이 작업을 정기적으로 반복 요청할 예정이다. **매번 새로
스캔해서 템플렛을 채운 새 파일을 만드는 것**이지, 이전 실행 결과 파일에 누적
추가하는 게 아니다 (겹치는 기간에 같은 추천이 다시 뽑혀도 정상 — 최신 취합본
하나로 대체되는 구조).

## 1. 이메일 검색

Gmail MCP (`mcp__claude_ai_Gmail__search_threads`, `get_thread`)로 검색한다.
기간은 사용자가 명시하지 않으면 최근 10일(`newer_than:10d`).

검색 쿼리 예시 (여러 번 넉넉하게 돌려서 놓치지 않도록 한다):

```
newer_than:10d (plenary OR lecturer OR nomination OR candidate OR 추천)
  (to:kimy@cern.ch OR to:kingmking@gmail.com
   OR from:secretariat@qm2027.kr OR to:secretariat@qm2027.kr)
```

```
newer_than:10d subject:(plenary OR lecturer OR nomination OR candidate)
```

```
newer_than:10d to:kimy@cern.ch
```

주의:
- `secretariat@qm2027.kr`가 보낸 `FW: Re: Invitation to the QM2027 Program
  Organizing Committee` 류 제목의 메일은 **POC 운영 관련 논의**(구성/역할 논쟁 등)인
  경우도 많다 — 실제 후보 이름·소속·주제가 나열된 메일만 추천으로 취급한다.
  (예: Andre Stahl의 "I agree with the POC proposal" 답장은 추천이 아니라
  POC 구성안에 대한 동의 표시일 뿐이므로 제외.)
- 순수 관리 메일(“XOC 미팅 안내”, “LOC 회의 안내”, POC 배정 관련 메일 등)도 제외.
- `get_thread`는 `messageFormat: PLAIN_TEXT`로 불러서 본문을 읽는다.

## 2. 추천 메일에서 정보 추출

추천 메일 하나당 다음을 뽑는다:

- **추천자(recommender)**: 이름 + 알 수 있으면 소속 (예: `Laura Tolos (ICE, CSIC)`).
  소속을 모르면 이름만.
- **후보자별**: Name, Affiliation/Position, Gender, Topic, Nationality.
  이메일에 명시 안 된 항목은 빈칸으로 둔다 (추측 금지).
- **순위(Priority)**:
  - 추천자가 순위를 전혀 안 적었으면 → 후보 전원 **1순위**로 채운다
    (사용자 지침: "순위가 안 적혀 있으면 모두 1순위라고 써").
  - 추천자가 번호(1, 2, 3 등)를 매겨서 나열했으면 → 그 번호를 그대로 순위로 쓴다.
  - 번호와 별도로 "top priority" 같은 강조 표시가 특정 후보에 붙어 있으면, 나열
    순서(번호)는 그대로 두고 그 후보의 **Remarks**에 강조 내용을 남긴다 (번호를
    임의로 재배열하지 않는다 — 애매하면 원문 순서를 존중).
- **Plenary vs Lecturer 구분**: 이메일 본문에 "Lecture"/"Student Day"라고 명시된
  후보는 Lecturer 시트로, "Plenary"라고 명시되거나 구분 없이 뭉뚱그려 온 경우는
  Plenary 시트로 넣는다.

3명 미만을 추천한 경우, 그 추천자의 3행 블록 중 나머지 행은 이름/소속 등 전부
빈칸으로 남긴다 (Priority 열의 사전 채워진 1/2/3 숫자는 템플렛 기본값이므로 건드릴
필요 없음 — 옆 칸이 비어 있으면 데이터 없음으로 읽힌다).

## 3. 대상 파일 / 시트 구조

템플렛 경로 (Google Drive 로컬 마운트):
```
/Users/yongsunkim/Library/CloudStorage/GoogleDrive-kingmking@gmail.com/My Drive/개인서류 drive/QM2027/QM2027_IAC_Recommendation for plenary.xlsx
```

시트 구조:
- **`IAC Recommendations`** (Plenary speaker): 헤더가 2행
  (`Recommender (Affiliation)`, `Priority`, `Name`, `Affiliation / Position`,
  `Gender`, `Topic`, `Nationality`, `Remarks`), 3행부터 3행 단위 블록이 5개
  (3~5, 6~8, 9~11, 12~14, 15~17) — 추천자 최대 5명분.
- **`Lecturuer`** (Student/Junior Day Lecturer): 헤더가 8행, 9행부터 3행 단위
  블록이 5개 (9~11 … 21~23 근처, 실제 범위는 파일에서 확인).
- 추천자 이름은 블록의 첫 행(A열)에만 쓰고 나머지 2행은 비워둔다 (병합 셀
  아님, 관례상 첫 행에만 표기).
- 추천자가 5명을 넘으면 블록이 모자란다 — `scripts/fill_template.py`가 이 경우
  에러를 내고 멈추도록 짜여 있으니, 사람이 템플렛에 블록을 더 추가하거나 우선
  순위를 사용자와 상의한 뒤 진행한다 (임의로 기존 추천자를 덮어쓰지 않는다).

## 4. 채우기 실행

`scripts/fill_template.py`에 추출한 데이터를 JSON으로 넘겨서 실행한다
(openpyxl 필요 — 없으면 `python3 -m pip install openpyxl --user`).

```bash
python3 ~/claude-codes/skills/qm2027-plenary-recommendation/scripts/fill_template.py \
  --template "<템플렛 경로>" \
  --data data.json \
  --out filled.xlsx
```

`data.json` 예시:

```json
[
  {
    "sheet": "plenary",
    "recommender": "Laura Tolos (ICE, CSIC)",
    "candidates": [
      {"name": "Juan Torres-Rincon", "affiliation": "University of Barcelona",
       "gender": "Male", "topic": "Femtoscopy of light and heavy flavour",
       "nationality": "Spain"},
      {"name": "Sasa Prelovsek", "affiliation": "University of Ljubljana",
       "gender": "Female", "topic": "Heavy flavor and exotic hadrons in Lattice",
       "nationality": "Slovenia"},
      {"name": "Sophia Han", "affiliation": "Tsung-Dao Lee Institute",
       "gender": "Female", "topic": "Equation of State in Neutron Stars and Mergers",
       "nationality": "China"}
    ]
  },
  {
    "sheet": "plenary",
    "recommender": "João Barata",
    "candidates": [
      {"priority": 1, "name": "Xoan Mayo", "affiliation": "MIT (postdoc)",
       "topic": "High-pT probes / jet quenching", "nationality": "Spain"},
      {"priority": 2, "name": "Wenyang Qian", "affiliation": "CCNU (Assistant Professor)",
       "topic": "Quantum computing for heavy-ion physics", "nationality": "China",
       "remarks": "Recommender noted this as 'top priority'"},
      {"priority": 3, "name": "Oscar Garcia Montero",
       "affiliation": "IGFAE, Santiago de Compostela (postdoc)",
       "topic": "Early stages of heavy-ion collisions"}
    ]
  },
  {
    "sheet": "lecturer",
    "recommender": "João Barata",
    "candidates": [
      {"priority": 1, "name": "Liliana Apolinario",
       "affiliation": "LIP, Portugal (junior scientist)", "gender": "Female",
       "topic": "Hard probes", "nationality": "Portugal"}
    ]
  }
]
```

`candidates` 항목에 `priority`를 아예 안 넣으면(순위 미기재) 스크립트가 자동으로
전원 1로 채운다.

## 5. 저장

원본 템플렛은 건드리지 않는다. 결과는 같은 폴더에 **원본 파일명 + 날짜시간**으로
저장한다:

```
QM2027_IAC_Recommendation for plenary_YYYYMMDD_HHMM.xlsx
```

(예: `QM2027_IAC_Recommendation for plenary_20260826_0958.xlsx`, 날짜/시간은
실행 시점 기준 로컬 시각.)

## 6. 실행 후 확인

openpyxl로 다시 열어서 채워진 셀을 출력해 보고, 사용자에게 몇 명의 추천자·
몇 명의 후보를 찾았는지, 애매하게 판단한 부분(순위 해석, Plenary/Lecturer 구분
등)이 있으면 짧게 요약해서 보고한다.
