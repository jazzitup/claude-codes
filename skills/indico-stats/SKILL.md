---
name: indico-stats
description: "Indico(indico.cern.ch 등) 컨퍼런스 이벤트의 등록(registration)·초록(abstract) 제출 현황을 관리자 권한으로 조회해서 국가·소속·소속유형·트랙·Theory/Experiment 통계까지 정리한 HTML 대시보드를 만든다. 'Indico 등록 인원', '초록 접수 현황', '컨퍼런스 통계 html로' 요청 시 사용."
---

# Indico 등록/초록 통계 스킬

Indico 이벤트 관리자(administrator) 페이지에서 등록·초록 데이터를 모아 통계 대시보드
HTML을 만드는 스킬. 공개 이벤트 페이지에는 등록 인원수 정도만 보이고, 국가·소속·
Theory/Experiment 여부 같은 세부 통계는 관리자 로그인 후 각 등록/초록 상세 페이지에만
있다는 게 핵심 포인트.

## 0. 전제

- 대상 이벤트에 대한 Indico administrator/manager 권한 계정이 필요하다.
- 로그인은 CERN SSO 등 사용자 본인만 할 수 있다. Claude는 비밀번호를 대신 입력하지
  않는다 — `claude-in-chrome`으로 브라우저를 열어 로그인 화면까지만 이동시키고,
  실제 로그인은 사용자에게 맡긴다.
- 데이터 수집은 브라우저 자동화(`mcp__claude-in-chrome__*`)로, HTML 렌더링은 이
  스킬의 `scripts/build_report.py`로 나눠서 처리한다.

## 1. 관리자 페이지 접속

```
https://<indico-host>/event/<event-id>/manage/
```

공개 페이지(`/event/<event-id>/`)에서 시작해도 되지만, 국가/소속유형/카테고리 같은
필드는 `/manage/` 하위에서만 보인다. 로그인이 안 되어 있으면 SSO 로그인 페이지로
리다이렉트되니, 사용자에게 직접 로그인해 달라고 안내하고 완료될 때까지 기다린다.

## 2. 등록(Registration) 데이터 수집

1. 좌측 메뉴 `Organisation > Registration` → 등록 폼의 `Manage` 클릭 →
   `Registrations <N>` 클릭하면 목록 페이지(`/manage/registration/<form_id>/registrations/`).
2. 목록 페이지의 `get_page_text`로 ID/이름/이메일/소속/등록일/상태를 한 번에 뽑을 수
   있다. 상단의 두 숫자(예: `11` / `1`)는 활성 등록 수 / 철회(withdrawn) 수.
3. **국가·소속유형(Country / Position-Registration Type)은 목록에 안 나온다.** 각
   등록자 행의 링크(`/manage/registration/<form_id>/registrations/<reg_id>/`)를
   열어야 "Country of Region", "Position/Registration Type" 같은 필드가 보인다.
   등록자가 10명 안팎이면 전부 열어서 `get_page_text`로 긁는 게 제일 빠르고 정확하다
   (필드 커스텀 리스트 UI로 컬럼을 추가하는 것보다 안정적).
4. Withdrawn 상태인 등록은 명단에는 포함하되, 국가/유형 등 **활성 통계 집계에서는
   제외**한다 (공개 페이지 숫자와 맞춰야 함).
5. **동일인이 여러 건으로 등록된 경우(이름+소속으로 판단, 보통 중복 등록 후 하나를
   철회)** 활성 집계에는 당연히 1건만 남지만, 명단 테이블에는 두 행이 그대로 보여서
   착각을 유발한다. 철회된 쪽 `roster` 항목에 `duplicate_note`(예: `"중복, #11과 동일인"`)를
   달아 스크립트가 이름 옆에 배지로 표시하게 한다.

## 3. 초록(Abstract) 데이터 수집

1. 좌측 메뉴 `Workflows > Call for Abstracts` → 마감일(scheduled to close) 확인 →
   `List of abstracts`의 `Manage` 클릭하면 목록(`/manage/abstracts/list/`).
2. 목록 페이지에서 ID/제목/상태(Awaiting Review 등)/트랙/제출 유형은 `get_page_text`로
   바로 나온다.
3. **Category(Theory/Experiment)와 Country/Affiliation은 목록에 없다.** 각 초록
   상세 페이지(`/manage/abstracts/<abstract_id>/`)를 열어야 "More information" 밑에
   `Category: Theory` 같은 필드와 (있다면) `Affiliation:` / `Country:` 필드가 보인다.
   상세 페이지 링크는 목록 페이지를 `read_page`(filter: interactive)로 읽으면
   `/manage/abstracts/<numeric_id>/` 형태로 전부 나온다.
4. **주의**: Country/Affiliation 필드는 이벤트 진행 중 양식에 추가되는 경우가 많다.
   즉 초록 제출 시점에 따라 이 필드가 없는 건이 섞여 있을 수 있다. 그런 경우
   같은 발표자(Speaker)의 등록(registration) 상세 페이지에 있는 "Country of Region"으로
   대조해서 채우고, 등록 기록도 없으면 "확인 불가"로 남긴다 — 없는 데이터를 추정해서
   채우지 않는다.
5. 여러 상세 페이지를 열 때는 `browser_batch`로 `navigate` + `get_page_text`를
   묶어서 한 번에 처리하면 왕복이 줄어든다.
6. **등록(registration) 양식에는 보통 Theory/Experiment 필드가 없다.** "등록자 중
   Theory/Experiment가 몇 명이냐" 같은 질문을 받으면, 등록자 이름과 초록 제출자
   이름(및 소속)을 대조해서 일치하는 사람만 그 초록의 카테고리를 붙여준다. 나머지
   등록자는 초록을 안 냈거나 이름이 안 맞는 것이므로 "불명"으로 남기고, Experiment로
   추정하지 않는다 (이 컨퍼런스는 Theory 초록만 들어온 상태일 수도 있고, 단순 참가자일
   수도 있음).

## 3-1. 이전 리포트 대비 변화 (정기 체크 시 기본 포함)

**"오늘 상황 체크해줘" 같은 정기 리포트 요청에는 항상 직전 리포트 대비 변화를
포함한다.** 같은 디렉터리(예: `qm2027/`)에 날짜가 찍힌 이전 `status_report_*.html`
파일이 있으면 그게 비교 기준이다 — 파일명의 날짜/시간이 곧 "지난 리포트" 시점이며,
별도로 "지난주" 스냅샷이 없다면 이 파일을 기준으로 삼고 그 사실을 리포트에 명시한다
(예: "지난주 별도 스냅샷은 없어 가장 최근 리포트(2026-08-02)와 비교"). 직전 리포트가
없으면 이 섹션은 생략.

비교 방법:
- 등록: 활성 인원 수(active_count)를 단순 대조. 사람 대조가 필요하면 이름으로.
- 초록: 전체 건수와 트랙별 건수를 대조. 신규 초록은 ID/제출일로 식별해서
  `comparison.new_abstracts`에 그대로 넣는다(리포트에 "신규 제출 초록" 표로 강조됨).
- 상태 변화(Awaiting Review → Accepted 등)가 있으면 `comparison.note`에 문장으로
  적는다. 스크립트가 자동으로 계산하지 못하는 것은 전부 이 free-text로 보완한다.

## 4. 통계 집계 → JSON

수집한 값을 아래 스키마의 JSON으로 정리한다. 이 JSON을 `scripts/build_report.py`에
넘기면 HTML이 나온다.

```jsonc
{
  "event": {
    "title": "행사명", "subtitle": "부제(선택)", "dates": "2027-03-21 ~ 27",
    "venue": "장소", "indico_url": "https://indico.cern.ch/event/<id>/manage/",
    "as_of": "2026-07-31"
  },
  "registration": {
    "active_count": 11, "total_submitted": 12,
    "by_state": {"Awaiting payment": 10, "Completed": 1, "Withdrawn": 1},
    "by_country": {"South Korea": 3, "China": 3},
    "by_position": {"Faculty": 7, "Staff": 2, "Student": 2},
    "roster": [
      {"id": "#9", "name": "In Kwon Yoo", "affiliation": "Pusan National University (KR)",
       "country": "South Korea", "position": "Faculty", "date": "2026-06-20",
       "state": "Awaiting payment"}
    ]
  },
  "abstracts": {
    "total": 8, "deadline": "2026-09-30 23:59 Asia/Seoul",
    "by_track": {"Collective Dynamics": 2, "Jets": 1},
    "by_category": {"Theory": 8, "Experiment": 0},
    "by_country": {"China": 2, "India": 1},
    "country_note": "국가 필드가 없는 제출건은 동일 발표자의 등록 정보로 대조함",
    "list": [
      {"id": "#6", "title": "제목", "track": "Chirality", "category": "Theory",
       "country": "—", "type": "Contributed Oral", "state": "Awaiting Review"}
    ]
  },
  "redact_emails": true
}
```

`by_state` / `by_country` / `by_position` / `by_track` / `by_category`는 순서가
곧 막대그래프 순서가 된다(값 큰 순으로 미리 정렬해서 넣을 것 — 스크립트는 재정렬하지
않는다).

## 5. HTML 생성

```bash
python3 scripts/build_report.py --input data.json --output report.html
```

- 외부 의존성 없음(표준 라이브러리만 사용).
- `dataviz` 스킬의 검증된 팔레트(카테고리 6색 + status 색)를 그대로 내장하고 있어
  라이트/다크 테마 모두 대비 기준을 통과한다. 막대 폭은 각 그룹 내 최댓값 대비 상대
  비율로 자동 계산된다.
- 등록자 이메일 주소는 기본적으로 출력하지 않는다(`redact_emails: false`로 명시하면
  포함 가능 — 로컬 파일로만 쓸 때 한정).

## 6. 개인정보 주의

등록자 실명·소속·결제상태, 초록 발표자 소속 국가 등은 관리자 로그인으로만 보이는
정보다. 결과 HTML을 온라인(Artifact 등)에 publish하기 전에는 반드시 사용자에게
알리고 확인받는다 — 기본은 비공개라도 링크 공유 시 노출될 수 있기 때문이다.

**이 스킬의 작업 과정에서 실제 등록자/초록 데이터가 담긴 예시 파일을
`examples/`(또는 그 밖의 리포지토리 경로)에 절대 저장하지 않는다.** 통계 집계용
JSON(`data.json` 등)과 결과 HTML은 항상 스크래치패드나 사용자가 명시적으로 지정한
로컬 경로에만 만들고, 스킬 리포지토리 안에는 커밋하지 않는다. 예시나 템플릿이
필요하면 실명·소속·이메일 등을 전부 가상의 값으로 바꾼 더미 데이터만 사용한다.
과거에 실제 데이터가 담긴 예시 파일(`quark_matter_2027.json`)이 실수로 커밋되었다가
git 히스토리까지 재작성해서 제거한 적이 있다 — 같은 실수를 반복하지 않는다.
