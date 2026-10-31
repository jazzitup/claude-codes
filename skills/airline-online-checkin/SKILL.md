---
name: airline-online-checkin
description: "항공편 온라인 체크인을 Chrome 브라우저 자동화(claude-in-chrome MCP)로 대신 해 주는 스킬. 체크인 창이 언제 열리는지 계산해서 알려 주고, 열리면 예약번호·성으로 조회 → 위험물 신고 → APIS(성별·생년월일·여권) → 좌석 선택(무료 창가 맨 앞자리) → 탑승권 화면 캡처 → 출장 폴더에 저장 + 본인 이메일로 PDF 발송까지 한다. 여권번호·주민번호·카드번호는 절대 대신 입력하지 않고 그 칸만 사용자에게 넘긴다. Uzbekistan Airways(HY, uzairways.com → digital.uzairways.com/ssci) 절차가 1차 검증됨(2026-10-31, HY516 ICN→TAS). '체크인 해', '비행기 체크인 되나 봐', '창가 자리 잡아', '탑승권 저장해' 요청 시 사용. 예약 정보는 Gmail의 Expedia/항공사 확정 메일에서 찾는다."
---

# 항공편 온라인 체크인 (브라우저 자동화)

## 0. 원칙 (안전)

- **사용자 본인 입력 칸**: 여권번호(Document number), 주민등록번호, 카드번호·결제 정보는
  Claude가 절대 입력하지 않는다. 요청받아도 "그 칸만 직접 입력해 달라"고 넘긴다.
  성별·생년월일·문서 종류·만료일·발행국은 사용자가 명시적으로 허락하면 입력해도 된다.
- **결제 없음**: 좌석은 "free of charge"로 표시된 것만 고른다. 결제 화면이 나오면 즉시 뒤로 가서
  좌석 없이 체크인만 끝낸다.
- **동의 버튼**("I agree and continue", 위험물 신고 등)은 본인 신고이므로 사용자에게 한 번 확인한 뒤
  누른다(권한 분류기가 막으면 사용자가 직접 누르게 하고 다음 화면부터 이어받는다).
- 이메일 발송은 **사용자 본인 주소**로만, 사용자가 허락한 경우에만.
- 개인정보 참조 파일 위치는 메모리(`reference-personal-info-file`)에 있다. 값은 어디에도 기록하지 않는다.

## 1. 예약 정보 찾기

Gmail MCP `search_threads` 로 `(항공사명 OR 편명) newer_than:120d` 검색 → Expedia/항공사 확정 메일에서
- 편명·날짜·시각, **항공사 예약번호(PNR, 6자리)**, **e-ticket 번호(13자리)**, 승객 성, 요금 규정
  (수하물 포함 여부, "Seat choice for a fee" 등)을 읽어 둔다.

## 2. 체크인 창 계산

항공사 규정(uzairways: 출발 23시간 55분 전 오픈, 국제선 2시간 전 마감; 공항 카운터는 3시간 전 오픈,
40분 전 마감)으로 **현지 시각 기준** 오픈 시각을 계산해 사용자에게 알린다. 너무 이르면 포털이
"Check-in opens in N hours" 를 보여 준다 → 그때는 `pending-tasks/` 에 대기 작업 파일을 만들어
(이 저장소의 pending-tasks 규칙) 다음 세션에 자동으로 뜨게 하거나 CronCreate 로 리마인더를 건다.

## 3. Uzbekistan Airways 절차 (검증됨)

도구: `ToolSearch select:mcp__claude-in-chrome__tabs_context_mcp,navigate,computer,find,form_input,get_page_text`.
`tabs_context_mcp{createIfEmpty:true}` → 새 탭에 열기.

1. `https://www.uzairways.com/en/online-registration`
   - "Identification type" 콤보 → `form_input` 으로 **By booking** (바꾸면 Last name 칸이 비워짐 →
     다시 `form_input` 으로 성 입력). Booking number 에 PNR → **Check in**.
   - 모달 "O'rindiq tanlash / How would you like to check in": *Register without a seat selection*
     (무료 자동배정) 또는 *Data for a seat selection*(티켓번호·성·통화 USD → Seat selection).
     2026-10-31 에는 후자가 바로 `digital.uzairways.com/ssci/journey-selection` 으로 넘어갔고
     **그 포털 안에 무료 좌석 지도가 있었다**(auxiliary 사이트의 유료 지도가 아님). 그 전날(10-30)에는
     auxiliary.uzairways.com 의 "추가 서비스" 지도가 떴고, 가는 편 대신 오는 편(fid=2) 지도만 보였음 —
     거기서 고른 좌석은 실제 체크인에 반영되지 않았다(13A 를 골랐지만 체크인 때 34G 자동배정).
2. `digital.uzairways.com/ssci/...` 포털 (기본 러시아어 → 상단 언어 버튼에서 **English (EN)**)
   - Journey selection: 해당 편의 **Check in** (오픈 전이면 "Check-in opens in …" 라벨만 있음)
   - Passenger selection: 승객 체크 확인 → Continue
   - Dangerous goods: **I agree and continue** (사용자 확인 후)
   - Regulatory details (APIS): Nationality(자동 채워짐) / Personal details(성별 radio, 생년월일
     dd/mm/yyyy → Save personal details) / Travel document(Document type 는 `mat-select` 라 `form_input`
     불가 → 클릭해서 Passport 선택, **Document number 는 사용자가 직접**, expiry dd/mm/yyyy, issuing
     country 는 자동완성 콤보에 "Korea" 입력 → South Korea) → Save travel document → Continue
   - Seatmap: 이 시점에 이미 "You are checked in!" + 자동배정 좌석. 범례: 빨강 = unavailable,
     **하늘색 = available free of charge**, 주황 = emergency row. B787-8 이코노미 창가 = **A·J열**,
     11–24열(앞 캐빈)·31–42열. 하늘색 중 가장 앞 A(없으면 J) 클릭 → 상단 승객 칩의 좌석이 바뀜 →
     **Confirm seat selection and continue**. (HY516 10-31: 11–23A/J 전부 빨강, 24A 가 첫 무료 창가)
   - Overview: "Checked in", Boarding time 표시. **View boarding passes** → 탑승권 카드
     (편명·터미널·출발/탑승 시각·좌석·QR). `computer zoom` 으로 카드 영역만 `save_to_disk:true` 캡처 →
     출장 폴더로 복사(`HY516_boarding_pass_YYYY-MM-DD_seatXX.png` 식 이름).
   - **Send boarding passes** → "Send by email in PDF format" 체크 → 이메일 칸이 예약 이메일로
     **대문자로 미리 채워져 있음** → `type` 하면 뒤에 붙어 "valid email" 오류 → `form_input` 으로
     값을 통째로 바꾼 뒤 Send → Overview 에 "Boarding passes were successfully sent".
   - **Manage baggage**: "Hold baggage — N bags included, N× 23kg" 와 Checked bags 카운터(기본 0).
     사용자가 부칠 가방 수만큼 **+** 로 올리고(포함 수량 안이면 무료) **Confirm**. 포함 수량을 넘기면
     결제로 이어지므로 멈춘다. 실제 가방은 공항 bag drop 에서 맡긴다.
3. 보고: 좌석, 탑승 시각, 터미널, 탑승권 저장 경로·이메일 발송 여부, 공항 도착 권장
   (수하물 있으면 출발 3시간 전 카운터 오픈, 40분 전 마감).
4. 뒷정리: pending-tasks 파일이 있었으면 `pending-tasks/done/` 으로 `git mv` + commit + push.

## 4. 다른 항공사

절차는 비슷하다(조회 → 승객 → 신고 → APIS → 좌석 → 탑승권). 항공사별로 검증되면 이 파일에
절(§3 과 같은 형식)을 추가한다. 좌석 지도의 무료/유료 구분은 반드시 **범례(legend)** 로 확인한다.
