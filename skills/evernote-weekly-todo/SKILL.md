---
name: evernote-weekly-todo
description: "사용자의 Evernote에서 'weekly todo's' 계열 노트(제목이 'June 4', 'July 3', 'August 2'처럼 <월 이름> <주차번호>인 노트)를 새 주차용으로 만든다. 전용 템플렛 노트(제목이 'weekly todo template ...'이고 attributes.isTemplate:true)를 찾아 표 구조를 그대로 옮기고, 대상 주의 일~토 날짜를 표 안에 채워 넣는다. 매주 금요일 오전 9시(KST)에 claude.ai 예약 routine으로도 자동 실행된다. '이번 주 위클리 투두 노트 만들어줘', '<월> <N>주차 노트 만들어', 'weekly todo 다음 주 걸로 만들어줘', 'X월 X일 템플렛 써서 넣어줘' 요청 시 사용."
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
  실행 로그에 명확히 남기도록 프롬프트에 지시해 뒀다. `claude.ai/customize/connectors`
  에서 Evernote를 연결하면 별도 조치 없이 다음 실행부터 정상 동작한다.

## 9. 개인정보 주의

템플렛 노트의 오른쪽 참고 링크 칸에는 `evernote:///view/...` 형태의 개인 노트
링크, 그리고 요일 칸의 반복 일정에는 실제 회의명·개인 zoom/indico 링크(비밀번호
쿼리스트링 포함)가 들어 있을 수 있다. 이런 실제 값은 **작업 중 로컬 스크래치패드
파일이나 Evernote 노트 안에서만** 다루고, 이 스킬 저장소(공개 GitHub repo)의
SKILL.md·예시 파일·routine 프롬프트 등에는 실명·실제 URL·노트 GUID를 절대 적지
않는다 — 위 섹션들의 설명은 전부 구조 설명일 뿐, 실제 값은 매번 `get_note`로
그때그때 읽어와야 한다.
