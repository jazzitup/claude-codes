---
from_epoch: 1793400900
until_epoch: 1793479500
window_kst: 2026-10-31 07:55 ~ 2026-11-01 05:45
---
# 대기 작업: Uzbekistan Airways HY516 온라인 체크인 (2026-10-31 아침)

사용자(김용선 교수)가 2026-10-30에 요청한 작업이다: "내일 아침 8시에 내가 다른 컴퓨터에서
아무 세션이나 띄우면 체크인 하게 만들어". 이 파일이 세션 시작 컨텍스트로 주입됐다면 지금이
체크인 가능 시간대라는 뜻이다. **세션 시작 직후, 사용자가 다른 말을 꺼내기 전에 먼저
"HY516 체크인을 지금 진행하겠습니다"라고 존댓말로 알리고 바로 시작한다.** 사용자가 다른
일을 시키면 그 일과 병행하지 말고 체크인을 먼저 끝낸다(체크인은 몇 분이면 된다).

## 항공편 정보 (Gmail의 Expedia 확정 메일, 2026-09-08 기준)
- 가는 편: Uzbekistan Airways **HY516**, 2026-11-01(일) **ICN 07:50 → TAS 11:00**, Economy
- 오는 편: HY511, 2026-11-05(목) TAS 22:30 → ICN 11-06 08:40 (이번 작업 대상 아님)
- 항공사 예약번호(PNR): **B4QROW** / e-ticket: **2507509232189** / 승객: Yongsun **Kim**
- Expedia 일정번호: 73539642248843

## 절차
1. 브라우저 자동화 도구를 확인한다. `mcp__claude-in-chrome__*`(ToolSearch로 로드) 또는
   `mcp__chrome-devtools__*` 중 연결된 쪽을 쓴다. 둘 다 없으면 사용자에게
   "이 컴퓨터엔 브라우저 자동화 MCP가 없어서 체크인을 못 합니다. 직접 하시려면
   https://www.uzairways.com/en/online-registration 에서 By booking → Kim / B4QROW"라고
   알리고 끝낸다.
2. 새 탭에서 https://www.uzairways.com/en/online-registration 을 연다.
   - Identification type 콤보박스를 **"By booking"**으로 바꾼다.
   - Last name: `Kim`, Booking number: `B4QROW` → **Check in** 버튼.
   - 로그인·비밀번호·카드번호는 어디에도 절대 입력하지 않는다(필요하지도 않다).
3. "Online check-in for the flight" 모달이 뜬다. 선택지 두 가지:
   - **Register without a seat selection** (좌석 자동 배정, 무료)
   - **Data for a seat selection** (ticket number / last name / payment currency → Seat selection).
     2026-10-30 테스트에서 이 경로는 auxiliary.uzairways.com 의 "추가 서비스" 좌석 지도로
     넘어갔고, 그때는 **오는 편(route=TASICN) 지도만** 보였다(가는 편 fid=1은 오는 편으로
     리다이렉트). 결제 통화를 고르게 하므로 유료일 수 있다.
4. 사용자의 희망: **창가 중 가장 앞자리, 단 무료일 때만.** ("무료면 13A해")
   - 먼저 Seat selection 경로로 들어가서(ticket `2507509232189`, last name `Kim`, currency USD)
     지도가 **가는 편(ICN→TAS)** 것인지 확인한다. 확인 방법: `javascript_tool`로
     `document.querySelector('input[name=route]').value` 를 읽어 `ICNTAS`여야 한다.
     `TASICN`이면 오는 편이므로 그 지도에서는 아무 좌석도 확정하지 말 것.
   - 가는 편 지도이면 Boeing 787-8 이코노미 기준 창가는 **A열과 J열**이다. 흰색(free) 칸 중
     가장 앞 줄의 A를 고른다(A가 없으면 같은 줄 J, 그다음 줄 순). 10-30 기준 오는 편 지도에서는
     11A·11J·12A·12J가 찼고 13A·13J가 가장 앞 빈 창가였다 — 가는 편은 다를 수 있으니 실제
     지도를 본다. 비상구 열(Emergency exit)과 노란색(paid) 칸은 피한다.
   - 좌석을 누르면 "Confirm your choice / Seat: 13A" 식 확인창이 뜬다. **가격이 0 또는 표시가
     없고 결제 화면으로 가지 않으면** Confirm. 결제(카드 입력)로 넘어가면 즉시 중단하고
     Return to booking → "Register without a seat selection"으로 무료 체크인만 하고, 좌석은
     자동 배정됐다고 사용자에게 알린다. 어떤 경우에도 결제하지 않는다.
   - 체크인 화면 안에서 좌석 지도가 직접 뜨는 구조로 바뀌어 있으면 같은 규칙(무료 창가 맨
     앞)으로 고른다.
5. 체크인이 끝나면 탑승권(boarding pass) 화면이나 PDF/이메일 발송 옵션이 나온다.
   - 이메일로 보내는 옵션이 있으면 kingmking@gmail.com 으로 보낸다(이 작업에 한해 허용).
   - PDF 다운로드는 사용자에게 한 번 물어보고 허락하면 ~/Downloads/ 에 저장한다.
   - 화면 스크린샷을 찍어 좌석 번호·탑승구·탑승 시각을 사용자에게 알린다.
6. 마무리 보고(존댓말): 체크인 완료 여부, 배정 좌석, 탑승권 전달 방법, 공항 도착 권장 시각
   (국제선 카운터 체크인 마감은 출발 40분 전, 수하물 부칠 거면 출발 3시간 전 카운터 오픈).
7. 완료(또는 사용자가 "됐다/그만"이라고 하면) 이 파일을 `pending-tasks/done/`으로 옮기고 커밋·푸시해서
   다른 컴퓨터에서 또 뜨지 않게 한다:
   `git -C ~/claude-codes mv pending-tasks/2026-10-31_uzairways-checkin.md pending-tasks/done/ && git -C ~/claude-codes commit -qm "Done: HY516 check-in" && git -C ~/claude-codes push -q`
   체크인이 아직 안 열렸다고 나오면(너무 이른 경우) 파일은 그대로 두고 사용자에게 몇 시에
   다시 열어달라고 말한다.
