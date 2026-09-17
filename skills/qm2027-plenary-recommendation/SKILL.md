---
name: qm2027-plenary-recommendation
description: "최근 N일(기본 10일, 마감 리마인더 직후엔 더 넓게)간 QM2027 Plenary/Lecturer 추천 이메일을 찾아 Google Drive의 'QM2027_IAC_Recommendation for plenary.xlsx' 계열 파일에 채워 넣는다. 이메일 검색은 기본적으로 Mac Mail.app(sejong.ac.kr/Google/cern mail 계정, AppleScript)을 쓰고, 사용자가 명시적으로 'Gmail'이라고 하면 Gmail MCP를 쓴다. 추천자당 최대 3명 규칙을 넘는 4번째 후보부터는 회색 글씨로 표시하고, 추천자 이름은 모든 행에 반복 기입한다. '정리해줘'든 기존 결과 파일을 가리키며 '업데이트 해'든 상관없이 **항상 파일명에 오늘 날짜/시간을 붙인 새 파일**로 저장한다 — 과거 스냅샷 파일은 절대 덮어쓰지 않는다. 'QM2027 추천 정리해줘', 'IAC 추천 엑셀 채워줘', '플레너리 추천 취합해줘', '이 파일 업데이트해' 요청 시 사용."
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

**기본은 Mac Mail.app** (AppleScript/osascript로 `Mail` 애플리케이션을 조작) 이다 —
사용자 지침: "메일을 물으면 mac 안의 mail client 을 말하는거야". Gmail MCP
(`mcp__claude_ai_Gmail__search_threads`, `get_thread`)는 사용자가 명시적으로
"Gmail"이라고 말했을 때만 쓴다.

Mail.app 계정은 `sejong.ac.kr` (yongsun@sejong.ac.kr), `Google`
(kingmking@gmail.com), `cern mail` (kimy@cern.ch) 세 곳을 모두 검색한다
(계정 목록은 `tell application "Mail" to repeat with acc in accounts` 로 확인
가능). 실제 추천 메일 대부분은 `secretariat@qm2027.kr` → `qm2027_coloc@googlegroups.com`
경유로 Google 계정 INBOX에 쌓인다.

기간은 사용자가 명시하지 않으면 최근 10일. 검색 예시 (AppleScript):

```applescript
set cutoffDate to (current date) - (30 * days)
tell application "Mail"
  repeat with accName in {"sejong.ac.kr", "Google", "cern mail"}
    set theAccount to account accName
    repeat with mb in mailboxes of theAccount
      set msgs to (messages of mb whose date received > cutoffDate and ¬
        (subject contains "Nomination" or subject contains "nomination" or ¬
         subject contains "Speaker" or subject contains "speaker"))
      -- collect accName, mailbox name, subject, sender, date, id
    end repeat
  end repeat
end tell
```

`content of message`는 첨부파일/서식을 잃으므로, 특정 메일에 xlsx 등 첨부가
있으면 `source of message`로 raw .eml을 저장한 뒤 Python `email` 모듈로
디코딩해서 첨부파일을 꺼낸다 (색상 정보가 필요한 xlsx 첨부의 경우 특히 중요 —
`content of message`로는 셀 배경색 같은 서식이 보존되지 않는다).

전체 후보 메일 목록을 얻었으면, ID 리스트를 만들어 한 번의 AppleScript 호출로
모든 본문(`content of message id X of mailbox Y`)을 텍스트 파일에 몰아
받는다 — 메일 하나씩 개별 호출하면 매우 느리다.

**대량 유입 주의**: 사무국이 "Sep. 10 마감" 같은 리마인더를 보내면 마감일
전후로 며칠 새 20~40통씩 추천 메일이 한꺼번에 쏟아진다. 10일 창으로는 부족할
수 있으니, 최근 미팅/리마인더 메일 날짜를 먼저 확인하고 그 이후 전체를
검색 범위로 잡는다.

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
  Plenary 시트로 넣는다. 한 추천자가 plenary 후보와 lecturer 후보를 한 메일에
  같이 보내는 경우가 흔하다 — 그러면 두 시트에 각각 별도의 블록으로 나눠 넣는다.
- **한 추천자당 최대 3명** 규칙이 있다 (LOC 공지: "nominations (max. 3) for
  Plenary speakers and Early-Career Researcher (Junior) Day lecturers,
  respectively" — Plenary 3명, Lecturer 3명 각각 별도 한도). 추천자가 이 한도를
  넘겨 4명 이상을 보내면(가끔 있음), **4번째 후보부터는 회색 글씨(폰트 색
  `FF808080`)로 표시**해서 한도 초과임을 시각적으로 표시한다 — 데이터 자체는
  지우지 않고 전부 보존한다.
- **개정(update) 메일**: 같은 추천자가 나중에 "update my nomination"처럼 이전
  추천을 수정/철회하는 메일을 보내면, **최신 메일의 내용으로 교체**하고
  Remarks에 "Updated nomination (날짜), superseding original ... list" 식으로
  이전 내용을 요약해 남긴다 (이전 것을 별도 행으로 남기지 않는다).

3명 미만을 추천한 경우, 나머지 행은 만들지 않는다 (고정 3행 블록이 아니라
후보 수만큼만 가변 길이로 기록 — 아래 3절 참고).

## 3. 대상 파일 / 시트 구조

템플렛 경로 (Google Drive 로컬 마운트):
```
/Users/yongsunkim/Library/CloudStorage/GoogleDrive-kingmking@gmail.com/My Drive/개인서류 drive/QM2027/QM2027_IAC_Recommendation for plenary.xlsx
```

시트 구조:
- **`IAC Recommendations`** (Plenary speaker): 헤더가 2행
  (`Recommender (Affiliation)`, `Priority`, `Name`, `Affiliation / Position`,
  `Gender`, `Topic`, `Nationality`, `Remarks`), 3행부터 데이터 시작.
- **`Lecturuer`** (Student/Junior Day Lecturer): 헤더가 8행, 9행부터 데이터
  시작.
- **원본 템플렛(빈 상태)은 추천자당 고정 3행 블록 × 5명분**으로 만들어져
  있지만, 이는 초기 목업일 뿐이다. **실제 데이터를 채울 때는 이 5블록/3행
  제약에 얽매이지 않는다** — 마감 리마인더 이후에는 추천자가 수십 명, 후보가
  100명을 넘기는 경우가 흔하므로, 추천자마다 실제 후보 수만큼만 행을 쓰고
  (1명이면 1행, 5명이면 5행 — 4번째부터는 위의 회색 규칙 적용) 필요한 만큼
  아래로 죽 이어서 적는다. 시트가 100행을 넘어가도 정상이다.
- **추천자 이름(A열)은 그 추천자의 모든 행에 반복해서 적는다** (블록 첫
  행에만 적고 나머지를 비워두지 않는다) — Excel에서 정렬/필터링해도 각 행이
  어느 추천자 것인지 바로 보이도록 하기 위함. 사용자 지침: "모든 행에
  추천자이름도 넣어버려."

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

기본 동작은 원본 템플렛을 건드리지 않고 같은 폴더에 **원본 파일명 + 날짜시간**
으로 새 파일을 저장하는 것이다:

```
QM2027_IAC_Recommendation for plenary_YYYYMMDD_HHMM.xlsx
```

(예: `QM2027_IAC_Recommendation for plenary_20260826_0958.xlsx`, 날짜/시간은
실행 시점 기준 로컬 시각.)

**"이 파일 업데이트해"라는 말도 새 날짜 파일을 만들라는 뜻이다** — 기존에
날짜가 붙은 특정 결과 파일의 경로를 사용자가 대면서 "업데이트 해"라고 해도,
그 파일을 직접 덮어쓰지 않는다 (2026-09-11에 실제로 이렇게 착각해서 기존
스냅샷 파일을 고쳐버렸다가 사용자에게 지적받고 복구한 사례 있음 — 각 결과
파일은 그 시점의 스냅샷으로 보존되어야 하고, "업데이트"는 "최신 이메일까지
다시 스캔해서 새로 취합"이라는 뜻이지 "이 파일을 편집"이라는 뜻이 아니다).
절차:
1. 사용자가 가리킨 기존 파일을 열어 이미 들어있는 추천자/후보를 읽어 최신
   상태를 파악한다 (읽기 전용 참고 — 이 파일 자체는 건드리지 않는다).
2. 이메일을 다시 스캔해서 (a) 기존에 없던 새 추천자, (b) 기존 추천자가 보낸
   개정(update) 메일을 찾는다.
3. 기존 데이터 + 신규/개정 데이터를 합쳐서 위 3절의 가변 길이 방식으로 만든
   전체 데이터를, **오늘 날짜/시각이 붙은 새 파일**에 쓴다.

**재실행 스케줄링**: 사용자가 "n시간 후에 또 업데이트해" 라고 하면, 한 번만
반복할지 계속 반복할지 명확하지 않으면 반드시 먼저 물어본다 (2026-09-11
사례: "다음 1회만, 그 이후엔 별도 요청 없으면 종료"로 답함 — 매번 다시
확인하는 것이 안전, 사용자가 "이번엔 계속 반복"이라고 명시하지 않는 한
one-shot으로 간주).

## 6. 실행 후 확인

openpyxl로 다시 열어서 채워진 셀을 출력해 보고, 사용자에게 몇 명의 추천자·
몇 명의 후보를 찾았는지, 애매하게 판단한 부분(순위 해석, Plenary/Lecturer 구분
등)이 있으면 짧게 요약해서 보고한다.
