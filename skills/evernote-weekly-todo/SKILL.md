---
name: evernote-weekly-todo
description: "사용자의 Evernote에서 'weekly todo's' 계열 노트(제목이 'June 4', 'July 3', 'August 2'처럼 <월 이름> <주차번호>인 노트)를 새 주차용으로 만든다. 전용 템플렛 노트(제목이 'weekly todo template ...'이고 attributes.isTemplate:true)를 찾아 표 구조를 그대로 옮기고, 대상 주의 일~토 날짜를 표 안에 채워 넣는다. 지난 15일간의 메일(Gmail + 로컬 Mail.app의 sejong.ac.kr/CERN 계정)을 훑어 대상 주에 마감·일정이 있는 항목을 Urgent items 체크리스트에 자동으로 추가한다. Evernote MCP(https://mcp.evernote.com/mcp)가 로컬 Claude Code 세션에 연결되어 있으면 실제로 노트를 생성/수정한다 — 연결 상태·설정 방법은 10절 참고. 매주 금요일 오전 9시(KST)에 claude.ai 예약 routine으로도 자동 실행된다(단, routine은 Gmail만 스캔 가능하고, 별도로 클라우드 커넥터에도 Evernote가 연결되어 있어야 함 — 10절). '이번 주 위클리 투두 노트 만들어줘', '<월> <N>주차 노트 만들어', 'weekly todo 다음 주 걸로 만들어줘', 'X월 X일 템플렛 써서 넣어줘', '메일 확인해서 리마인더 넣어줘' 요청 시 사용."
---

# Evernote 주간(Weekly) Todo 노트 생성

이 사용자는 Evernote의 한 노트북(이하 "weekly todo's" 노트북)에 매주 한 개씩
"<월 이름> <주차번호>" 형태(예: `June 4`, `July 3`, `August 2`)로 주간 할일 노트를
만든다. 이 스킬은 그 다음 주 노트를 기존 형식 그대로 새로 만드는 절차다.

## 0. 핵심 아이디어

- 표 구조를 손으로 다시 만들지 않는다. **항상 실제 템플렛 노트를 읽어서 그 ENML을
  그대로 재사용**한다 — 표 폭, 색상, 링크 컬럼 등은 사람이 Evernote 에디터에서
  다듬어 놓은 값이라 재현하면 미묘하게 달라진다.
- 날짜만 요일별로 채워 넣고, 나머지 구조(반복 일정, 오른쪽 참고 링크 칼럼 등)는
  템플렛에 있는 그대로 옮긴다.
- 노트 제목(월 + 주차번호)은 아래 2단계의 고정 규칙으로 계산한다 — 과거 노트 중
  이 규칙과 어긋나 보이는 예시가 있어도(사람이 수동으로 만들다 보니 생긴 예외)
  이 규칙을 우선한다.

## 1. 노트북 · 템플렛 · 예시 노트 찾기

1. `mcp__evernote__search_notebooks`로 "weekly todo" 관련 노트북을 찾거나, 이미
   알고 있는 주간 노트(예: 최근 `intitle:"July"` 검색 결과) 하나를 열어
   `notebookId`를 확인한다.
2. 그 노트북 안에서 `search_notes({query: "nbGuid:\"<notebookId>\""})`로 최근 노트
   목록을 훑는다. 제목이 "weekly todo template ..."인 노트가 보통 하나(또는 과거
   버전이 여러 개) 있다 — **가장 최근에 생성/수정된 것 중 `get_note`로 확인했을 때
   `attributes.isTemplate === true`인 노트가 진짜 템플렛**이다. isTemplate이 없는
   동명의 노트는 예전에 실제로 썼던 주간 노트가 우연히 같은 제목으로 남아있는
   것일 수 있으니 attributes를 꼭 확인한다.
3. 최근 주차 노트(예: 지난주 노트)도 하나 열어서 실제 예시로 비교해보면, 템플렛과
   달리 요일 칸에 날짜 숫자가 채워져 있고 체크박스에 실제 완료 표시가 있는 걸
   확인할 수 있다. 이번 작업은 템플렛 쪽 구조 + 새 날짜를 쓰는 것이지, 지난주
   노트의 실제 할일 내용을 복사하는 게 아니다.

## 2. 노트 제목 규칙 (월 + 주차번호)

노트는 항상 그 주의 **일요일(첫날)** 을 기준으로 이름 붙인다.

- **월 이름** = 그 일요일 날짜 자체가 속한 달. 주가 월 경계를 넘어가서
  월~토가 다른 달에 속하더라도(예: 일요일이 3/31, 월요일이 4/1) **일요일의 달을
  그대로 쓴다** — "그 주 안에 날짜가 더 많이 속한 달"이 아니다.
- **주차번호** = 그 일요일이 그 달의 몇 번째 일요일인지(그 달의 1일 이후 첫
  일요일이 1주차, 그다음 일요일이 2주차, ...).

예:
- 일요일이 8/9(2026년 8월의 2번째 일요일) → `August 2`
- 일요일이 3/31이고 그 달에 일요일이 3/3, 3/10, 3/17, 3/24, 3/31로 5개면
  (즉 3/31이 3월의 5번째 일요일이면) → 월요일이 4/1로 넘어가더라도 `March 5`

계산 예시(파이썬 의사코드):

```python
def week_title(sunday_date):
    first_of_month = sunday_date.replace(day=1)
    # 그 달의 첫 번째 일요일 찾기
    offset = (6 - first_of_month.weekday()) % 7  # weekday(): Mon=0..Sun=6
    first_sunday = first_of_month + timedelta(days=offset)
    week_number = (sunday_date - first_sunday).days // 7 + 1
    return f"{sunday_date.strftime('%B')} {week_number}"
```

## 3. 대상 노트가 이미 있는지 확인

사용자가 "8월 2 만들어줘"처럼 제목을 먼저 만들어 두고 부탁하는 경우가 있다
(빈 노트만 미리 생성해 둠). `search_notes({query: "intitle:\"<제목>\""})`로 먼저
확인하고,
- 이미 빈 노트가 있으면 그 GUID로 바로 5단계(본문 채우기)로 넘어간다.
- 없으면 `mcp__evernote__create_note({title: "<월> <N>", notebookId})`로 새로
  만든다 (본문은 비어서 생성됨).

## 4. 표 구조 이해

주간 노트 본문은 보통 표 3개 + 구분용 `<div><br/></div>`로 이루어진다.

1. **Morning Routine 표** — 7일 헤더(Sun~Sat) + 빈 칸 한 줄. 날짜를 넣지 않는다.
2. **Week / Morning Study / Jogging / Night writing 표** — 왼쪽에 Sun~Sat 요일
   라벨, 오른쪽 3칸(Morning Study, Jogging, Night writing)은 빈 칸. 여기도 날짜를
   넣지 않는다.
3. **Motto of the week / Urgent items 표(메인 표)** — 요일별로 한 행씩:
   - 요일 라벨 칸 (`Sun`, `Mon`, ...)
   - **날짜 + 할일 체크박스 칸** — `<div><br/></div>` 자리에 그 날짜 숫자를 넣는다.
     (예: `<div><br/></div><ul style="--en-todo:true;">...` →
     `<div>10</div><ul style="--en-todo:true;">...`)
   - `rowspan="7"`인 오른쪽 참고 링크 칸(Study log, 읽을거리, "On the list" 등) —
     Sun 행에만 존재하며 7일 전체에 걸쳐 있다. **내용을 새로 만들지 말고 템플렛의
     것을 그대로 복사**한다 (개인 노트 링크라 재생성 불가).

날짜가 들어가는 자리는 **메인 표(3번) 안의 7개 요일 행뿐**이다. 1·2번 표는 항상
빈 칸으로 둔다 — 실제 기존 노트들(`June 4`, `July 3` 등)이 그렇게 되어 있다.

## 5. 요일별 날짜 계산

2단계에서 구한 일요일을 `D`라 하면:

```
Sun = D, Mon = D+1, Tue = D+2, Wed = D+3, Thu = D+4, Fri = D+5, Sat = D+6
```

이 숫자들이 표에 그대로 들어간다 (월이 바뀌어도 숫자만 넣는다 — 노트 제목의
월과 표 안 날짜 숫자가 다른 달을 가리킬 수 있고, 그게 정상이다).

## 6. 본문 채워 넣기

1. 템플렛 노트의 `get_note` 결과에서 `content` 전체(3개 표 + 구분 div)를 그대로
   가져온다.
2. 메인 표의 7개 요일 행에서 날짜가 들어갈 `<div><br/></div>`를 각각 해당 숫자로
   바꾼다. 이 패턴은 표 안에 여러 번 나오므로(요일마다 한 번씩), 단순 전체
   치환(global replace)이 아니라 **각 요일 행의 문맥으로 유일하게 구분해서** 하나씩
   바꿔야 한다 — 요일 라벨(`Sun`, `Mon`, ...)이나 그 행에만 있는 문구를 앵커로 쓰면
   된다. 스크래치패드에 템플렛 원문을 파일로 저장해두고 `sed`/스크립트로 자리
   표시자(`SUN_DATE`, `MON_DATE`, ...)를 먼저 심어둔 뒤 한 번에 치환하면 실수가
   적다.
3. 완성된 본문을 대상 노트에 반영한다.
   - 새로 만든 빈 노트(본문이 `<div><br/></div>` 하나뿐)라면
     `mcp__evernote__edit_note({noteId, mode: "replace", find: "<div><br/></div>", content: <완성된 본문>})`
     한 번으로 충분하다 (그 노트 안에서 저 문자열이 유일하게 한 번만 나오기
     때문).
   - 이미 내용이 있는 노트를 고치는 거라면 `find`를 더 구체적으로 잡아야 한다
     (ENML은 byte-exact 일치가 필요 — `get_note`에서 그대로 복사).
4. `content`는 잘 정돈된 XML이어야 한다 — bare `&`, `<`는 반드시
   `&amp;`, `&lt;`로 이스케이프한다.

## 7. 검증

`get_note`로 다시 읽어서 7개 요일 행에 의도한 날짜가 정확히 들어갔는지, 오른쪽
링크 칸과 반복 일정 항목이 템플렛과 동일하게 보존됐는지 확인한다.

## 8. 자동 실행 (매주 금요일)

이 스킬은 claude.ai routine(`RemoteTrigger`/`schedule` 스킬로 생성한 cron
routine, 이름 "Evernote weekly-todo Friday prep")으로 **매주 금요일 오전 9시
(Asia/Seoul)** 에 자동 실행되도록 예약되어 있다. Cloud routine은 Anthropic
클라우드에서 정해진 시각에 도는 것이라 로컬 Claude Code 앱이 열려 있는지와
무관하게 실행된다 — "그날 Claude가 안 열려 있으면"을 걱정할 필요가 없다.

- 실행 시점 기준 "그다음 일요일"(금요일 + 2일)을 대상 주의 시작일로 계산한다.
- routine의 프롬프트는 이 SKILL.md에 의존하지 않는 완전 자체완결형이다(클라우드
  세션은 이 저장소를 체크아웃하지 않으므로, 절차 전체를 프롬프트 안에 인라인으로
  풀어 넣었다). 이 SKILL.md를 고치면 routine 프롬프트도 `RemoteTrigger`
  `action: "update"`로 함께 갱신해야 내용이 어긋나지 않는다.
- routine에는 아직 Evernote MCP 커넥터가 연결되어 있지 않다(연결된 커넥터
  목록에 Google Drive/Gmail만 있고 Evernote가 없음). 커넥터가 연결되기 전까지는
  routine이 금요일마다 실행은 되지만 Evernote 도구 호출에 실패하고, 그 사실을
  실행 로그에 명확히 남기도록 프롬프트에 지시해 뒀다. 애초에 **Evernote MCP는
  아직 공식 출시 전(대기자 명단 단계)이라 연결 자체가 불가능한 상태**다 — 자세한
  내용은 10절 참고.
- routine 프롬프트에는 Gmail 리마인더 스캔 단계(9.1절)가 추가되어 있다: 본문을
  채우기 전 `mcp__gmail__search_threads`류 도구로 지난 15일 메일을 훑어 대상
  주에 마감·일정이 있는 항목을 Urgent items에 추가로 넣는다. 단, routine은
  클라우드에서 돌기 때문에 로컬 Mail.app(sejong.ac.kr, CERN 계정)은 스캔하지
  못한다 — 그건 로컬 Claude Code 세션에서 이 스킬을 직접 실행할 때만 가능하다.

## 9. 이메일 리마인더 스캔 (Urgent items 자동 채움)

노트 본문을 채울 때, 지난 15일간의 메일을 훑어서 **대상 주(일~토)에 마감/일정이
있는 항목**을 찾아 메인 표의 해당 요일 행 체크리스트에 추가한다. 대상 계정은
4개이며, 접근 방법이 계정마다 다르다:

| 계정 | 주소 | 접근 방법 | 로컬 CLI | 클라우드 routine |
|---|---|---|---|---|
| Gmail | kingmking@gmail.com | `mcp__claude_ai_Gmail__search_threads` (claude.ai Gmail 커넥터) | 가능 | 가능 (이미 연결됨) |
| sejong.ac.kr | yongsun@sejong.ac.kr | 로컬 Mail.app, AppleScript(`osascript`) | 가능 | **불가능** |
| CERN | kimy@cern.ch (Exchange 계정) | 로컬 Mail.app, AppleScript(`osascript`) | 가능 | **불가능** |
| iCloud | kingmking@icloud.com | (필요시) 로컬 Mail.app, AppleScript | 가능 | **불가능** |

**중요한 제약**: 클라우드 routine(매주 금요일 자동 실행)은 Anthropic 클라우드
샌드박스에서 돌기 때문에 사용자의 로컬 Mac이나 Mail.app에 전혀 접근할 수 없다.
즉 sejong.ac.kr·CERN·iCloud 메일은 **이 스킬을 로컬 Claude Code 세션에서 직접
실행할 때만** 스캔할 수 있고, 자동 금요일 routine은 Gmail만 스캔한다. 이
비대칭은 실제 제약이니 사용자에게 숨기지 말고 그대로 알린다.

### 9.1 Gmail 스캔 (로컬·클라우드 공통)

```
mcp__claude_ai_Gmail__search_threads({
  query: "newer_than:15d in:inbox -category:promotions -category:social",
  pageSize: 50
})
```
결과 스니펫에서 날짜가 명시된(회의, 마감, 회신기한 등) 항목만 골라낸다. 광고성
뉴스레터·보안 알림(2FA, 로그인 알림)·arXiv 데일리 다이제스트 등은 제외한다.

### 9.2 sejong.ac.kr · CERN(Exchange) 스캔 (로컬 전용, AppleScript)

로컬 세션에서는 Bash로 `osascript`를 호출해 Mail.app을 스크립팅한다. 계정별
Inbox 메일박스 이름이 다르므로 (`mailbox "INBOX" of account "sejong.ac.kr"`,
`mailbox "Inbox" of account "Exchange"` — "Exchange"가 실제로는 cern.ch
Exchange 계정이다. 계정 표시 이름이 바뀌었을 수 있으니
`tell application "Mail" to get name of every account`로 먼저 확인) 아래
패턴으로 최근 15일 메일을 가져온다:

```applescript
set cutoffDate to (current date) - (15 * 24 * 60 * 60)
tell application "Mail"
  set mb to mailbox "INBOX" of account "sejong.ac.kr"
  set msgs to (messages of mb whose date received > cutoffDate)
  repeat with m in msgs
    -- (date received of m), (sender of m), (subject of m)
  end repeat
end tell
```

메일함이 크면 출력이 매우 길어지므로(수백 통), 전체를 그대로 컨텍스트에 읽지
말고 파일로 저장한 뒤 `grep -iE '요청|확인|deadline|due |meeting|마감|신청|제출|
reminder|urgent'` 등으로 1차 필터링하고, 그중 **제목이나 본문에 구체적 날짜가
박혀 있고 그 날짜가 대상 주(일~토) 안에 들어오는 것만** 최종 후보로 남긴다.
같은 스레드의 반복 RE/FW는 최신 것 하나만 남기고, 단순 정보성 공지(뉴스레터,
스팸 리포트, arXiv 다이제스트, 보안 알림)는 제외한다.

### 9.3 Urgent items에 반영

- 최종 후보 각각을, 마감/일정 날짜가 속한 요일 행의 체크리스트에 새 `<li>` 항목
  으로 추가한다 (날짜를 특정할 수 없으면 넣지 않는다 — 애매한 항목을 억지로
  아무 요일에나 넣지 않는다).
- 항목 텍스트는 "[메일] <한 줄 요약> (출처: <발신자 또는 요약>)" 형태로, 원래
  체크리스트 항목과 시각적으로 구분되게 한다.
- 템플렛에서 이미 있는 반복 항목·오른쪽 참고 링크 칼럼은 절대 건드리지 않는다
  — 이 단계는 순수 추가(additive)다.
- 노트를 채운 뒤 사용자에게 "이메일에서 자동으로 추가한 항목" 목록을 요약해서
  보여준다 (오탐이 있을 수 있으니 검토를 유도한다).

## 10. Evernote MCP 연결 상태 (2026-08-23 업데이트)

- **공식 Evernote MCP 서버가 출시됐다**: `https://mcp.evernote.com/mcp` (HTTP,
  OAuth). 2026-08-23 이전 버전의 이 문서는 "아직 waitlist 단계"라고 적어뒀는데
  그 사이 정식 출시된 것으로 보인다 — 과거 스냅샷을 과신하지 말 것(메모리/문서
  일반에 해당하는 주의사항).
- **로컬 Claude Code CLI 세션**에서는 다음으로 연결한다 (한 번만 하면 됨):
  ```
  claude mcp add --transport http evernote https://mcp.evernote.com/mcp
  claude mcp login evernote
  ```
  `claude mcp login`은 OAuth 리다이렉트를 로컬에서 직접 받아야 해서 **진짜
  인터랙티브 터미널**이 필요하다 — Claude Code 안에서 Bash 도구로 실행하거나
  `!` 프리픽스로 실행해도 둘 다 "stdin isn't a terminal"로 실패한다. 사용자가
  **Claude Code 밖의 순정 Terminal.app**에서 직접 실행해야 한다. 로그인 완료
  후에는 **그 시점 이후 새로 시작된 세션**에서만 `mcp__evernote__*` 도구가
  보인다 — 이미 떠 있던 세션은 도구 목록이 시작 시점에 고정되므로 재시작(또는
  `claude --continue`로 재시작 후 이어붙이기)이 필요하다.
- 스코프는 `read create write delete`로, 노트 생성/수정 전부 가능하다
  (`create_note`, `edit_note`, `search_notes`, `search_notebooks`, `get_note`
  등 — 커뮤니티 대안과 달리 읽기 전용이 아니다).
- `edit_note`는 전체 본문을 다시 보내는 게 아니라 `append`/`prepend`/`replace`
  중 하나로 ENML 조각만 보낸다. `replace`는 `find`가 노트 전체에서 정확히
  한 번만 매치해야 하므로, 요일 라벨(Sun/Mon/...)처럼 고유한 텍스트를 앵커로
  포함시켜야 한다. 새 노트를 한 번에 채울 때는 `create_note`(빈 노트 생성) →
  `edit_note(mode:"append", content:<전체 본문 fragment>)` 한 번으로 끝내는
  편이 7번의 개별 `replace`보다 간단하고 안전하다.
- **클라우드 routine(매주 금요일 자동 실행)은 별개 연결 체계다.** 위의
  `claude mcp login`은 이 Mac의 로컬 Claude Code 세션에만 적용되고, 클라우드
  routine은 claude.ai 계정 커넥터(`https://claude.ai/customize/connectors`)
  쪽에 Evernote가 연결돼야 그 routine의 `mcp_connections`에 붙일 수 있다.
  2026-08-23 기준 routine 쪽에는 아직 붙어 있지 않다 — 로컬 연결과는 별도로
  claude.ai 커넥터 페이지에서도 Evernote를 연결하고, `RemoteTrigger
  action:"update"`로 routine의 `mcp_connections`에 evernote 커넥터를 추가하고
  `allowed_tools`에 `mcp__evernote__*` 도구들을 넣어줘야 routine도 실제로
  쓰기 작업을 할 수 있다. 그 전까지는 routine이 여전히 8절의 "Evernote 연결
  안 됨" 경로를 탄다.

## 11. 개인정보 주의

템플렛 노트의 오른쪽 참고 링크 칸에는 `evernote:///view/...` 형태의 개인 노트
링크, 그리고 요일 칸의 반복 일정에는 실제 회의명·개인 zoom/indico 링크(비밀번호
쿼리스트링 포함)가 들어 있을 수 있다. 이런 실제 값은 **작업 중 로컬 스크래치패드
파일이나 Evernote 노트 안에서만** 다루고, 이 스킬 저장소(공개 GitHub repo)의
SKILL.md·예시 파일·routine 프롬프트 등에는 실명·실제 URL·노트 GUID를 절대 적지
않는다 — 위 섹션들의 설명은 전부 구조 설명일 뿐, 실제 값은 매번 `get_note`로
그때그때 읽어와야 한다.
