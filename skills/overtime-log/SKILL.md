---
name: overtime-log
description: 연구비 식대 영수증에 맞춰 세종대 산학협력단 '초과근무일지'(hwpx)를 만들고 PDF로도 저장한다. 기존 일지 hwpx를 복사해 근무일자와 시간만 바꾼다 — 평일 18:00~22:00, 주말 10:00~14:00. 서명 이미지는 원본에 들어 있어 그대로 유지된다. '초과근무일지 만들어줘', '이 영수증으로 초과근무일지', '초과근무 일지 pdf로' 요청 시 사용.
---

# 초과근무일지 (영수증 날짜 기준)

연구비 카드로 저녁/주말 식대를 쓰면 정산 때 그 날짜의 초과근무일지(서명 포함 PDF)가
필요하다. 매번 새로 쓰지 않고 이전 일지를 복사해 날짜·시간만 바꾼다.

## 1. 입력

- **영수증**: 보통 `Dropbox/01. 개인서류/2022- 중견과제/<YYYY>년 <M>월/` 안의
  `YYYY.MM.DD_<금액>원.jpg`. 영수증의 결제일(승인일시)이 근무일자가 된다.
- **템플릿**: 같은 과제 폴더(이번 달 또는 지난달)에 있는 가장 최근
  `초과근무일지 MM.DD.hwpx`. 사용자가 경로를 주면 그것을 쓴다.

## 2. 규칙

| 근무일 | 시간 |
|---|---|
| 평일(월~금) | `18:00 -` / `22:00` |
| 주말(토·일) | `10:00 -` / `14:00` |

- 요일은 `python3 -c "import datetime;print(datetime.date(Y,M,D).strftime('%A'))"`로 확인.
- 근무자·근무내용·근무장소는 템플릿 그대로 둔다(사용자가 따로 말하면 변경).
- 결과 파일: 영수증과 **같은 폴더**에 `초과근무일지 MM.DD.hwpx` + `초과근무일지 MM.DD.pdf`.
- 서명/날인 이미지는 템플릿 hwpx에 이미 포함 — 건드리지 않는다.

## 3. hwpx 수정 (구조 변경 금지, 텍스트만 치환)

```bash
S=<scratchpad>/ot; rm -rf $S; mkdir -p $S/un; cp "<템플릿.hwpx>" $S/src.hwpx
cd $S/un && unzip -q ../src.hwpx
grep -o '<hp:t>[^<]*</hp:t>' Contents/section0.xml   # 날짜·시간 run 확인
```
근무일자는 `<hp:t>2026</hp:t><hp:t>10</hp:t><hp:t>4</hp:t>`처럼 년/월/일이 각각의
run이고, 시간은 `<hp:t> 09:00 -</hp:t>` / `<hp:t>15:00</hp:t>` 두 run이다. Python으로
각 문자열이 **정확히 1번** 나오는지 assert한 뒤 치환한다(일·월 숫자가 다른 칸과
겹치면 앞뒤 run까지 포함해 유일하게 만든다). 재압축:
```bash
cd $S/un && zip -q -X -0 ../out.hwpx mimetype && zip -q -X -r ../out.hwpx . -x mimetype
python3 ~/.claude/skills/hwpxskill/scripts/validate.py ../out.hwpx
cp ../out.hwpx "<폴더>/초과근무일지 MM.DD.hwpx"
```

## 4. PDF 저장 (Hancom Office HWP, macOS)

```bash
open -a "Hancom Office HWP" "<폴더>/초과근무일지 MM.DD.hwpx"; sleep 6
osascript -e 'tell application "Hancom Office HWP" to activate' -e 'delay 1' \
 -e 'tell application "System Events" to tell process "Hancom Office HWP" to click menu item "PDF로 저장하기..." of menu 1 of menu bar item "파일" of menu bar 1'
```
저장 위치는 기본으로 문서 폴더, 이름은 문서명. **Return 키로는 저장되지 않는다** —
`window "PDF로 저장하기"`의 `entire contents`에서 role `AXButton`, title `저장`인
요소를 찾아 `click`한다. 몇 초 뒤 폴더에 PDF가 생겼는지 `ls`로 확인하고, PDF를
Read로 열어 날짜·시간·서명이 맞는지 검증한다.

- 한글 앱이 열려 있는 동안 사용자가 같은 창에서 작업 중일 수 있다 — 키 입력을
  보내기 전에 화면을 확인하고, 사용자가 "내가 했다"고 하면 바로 멈춘다.
- Hancom AppleScript는 close/count 미지원 → 문서 닫기는 생략하거나 Cmd+W.

## 5. 보고

만든 파일 2개 경로, 근무일자(요일)·시간, 템플릿과 달라진 점. 템플릿의 과제번호가
현재 진행 연차와 다르면(예: 템플릿 `-01`, 시스템상 현행 `-02`) 짚어준다.
