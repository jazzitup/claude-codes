---
from_epoch: 1794099098
until_epoch: 1795308698
window_kst: 2026-11-08 ~ 2026-11-22
---
# 대기 작업: iPhone 5s를 어린이 장난감용으로 초기화 (iOS 업데이트 알림 영구 제거)

사용자(김용선 교수)가 2026-11-08 아침 iMac 세션에서 요청했다가 "다른 컴퓨터에서 하겠다"고
미룬 작업이다. 이 파일이 세션 시작 컨텍스트로 주입됐다면, **세션 시작 직후 존댓말로
"iPhone 5s 초기화 대기 작업이 있습니다. 지금 진행할까요?"라고 한 번만 묻고**, 사용자가
하자고 하면 아래 절차대로 진행한다. 사용자가 다른 일을 시키면 그 일을 먼저 한다(급하지 않음).
작업이 끝나면 이 파일을 `pending-tasks/done/`으로 옮기고 push 한다.

## 기기 정보 (2026-11-08 usbmuxd/lockdownd로 확인)
- 이름 "Yongsun Kim's iPhone", **iPhone 5s** (ProductType iPhone6,1, N51AP), **iOS 11.4.1** (15G77)
- UDID `27479af1177ad0aaa33c5781458c966bcba41aab`
- iPhone 5s의 **마지막 iOS는 12.5.7**. 지금 뜨는 업데이트 알림이 그것이다. 12.5.7을 깔면
  더 올라갈 버전이 없어 알림이 영구히 사라진다. Mac에서 "복원"하면 Apple이 5s용으로
  서명하는 유일한 버전(12.5.7)이 자동으로 설치되면서 내용이 전부 지워진다.
- 이 작업을 요청한 iMac에는 이 폰의 Finder/iTunes 백업이 없었다(MobileSync 비어 있음).

## 사용자가 폰에서 먼저 해야 할 것 (Claude는 대신 못 함)
1. 남길 사진·자료가 있는지 묻는다. 있으면 Finder 백업을 먼저 한다(Finder > iPhone > 지금 백업).
2. **설정 > 맨 위 이름 > 나의 찾기 > "나의 iPhone 찾기" 끄기** — Apple ID 암호가 필요하며
   암호는 절대 Claude가 입력하지 않는다. 이걸 안 끄면 지운 뒤 활성화 잠금이 걸려 설정 화면에서
   같은 Apple ID 암호를 다시 요구한다. (대안: 설정 > 이름 > 로그아웃.)
3. 폰을 USB로 연결하고 잠금 해제, "이 컴퓨터를 신뢰"를 눌러 둔다.

확인 방법(선택): lockdownd에 `Domain: com.apple.fmip, Key: IsAssociated`를 GetValue 하면
"나의 iPhone 찾기"가 켜져 있는지(true) 알 수 있다. 아래 스크립트 참고.

## Claude가 Mac에서 하는 절차
1. 연결 확인 — `system_profiler SPUSBDataType`에는 iPhone이 안 잡히는 경우가 있다(2026-11-08
   실측). **usbmuxd에 직접 물어보는 게 확실하다**:
   ```python
   import socket, struct, plistlib
   def mux(p, s):
       d = plistlib.dumps(p); s.sendall(struct.pack('<IIII', 16+len(d), 1, 8, 1)+d)
       ln = struct.unpack('<IIII', s.recv(16))[0]; b = b''
       while len(b) < ln-16: b += s.recv(ln-16-len(b))
       return plistlib.loads(b)
   s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); s.connect('/var/run/usbmuxd')
   devs = mux({'MessageType':'ListDevices','ClientVersionString':'c','ProgName':'c'}, s)['DeviceList']
   # USB 항목의 DeviceID로 Connect(port htons(62078)) 후 lockdownd에
   # {'Request':'GetValue','Key':'ProductVersion'} 등을 big-endian 길이 접두 plist로 보낸다.
   ```
2. **Finder로 복원**: Finder 사이드바 > iPhone > 일반 탭 > **"iPhone 복원…"** 클릭 → 확인
   대화상자 "복원 및 업데이트". GUI 자동화는 System Events로 버튼을 누르되, 각 단계의
   스크린샷을 찍어 확인하고 **누르기 전에 사용자에게 "지금 지웁니다"라고 한 번 알린다.**
   (Apple Configurator의 `cfgutil restore`가 설치돼 있으면 그것도 된다; 없으면 Finder.)
   - 12.5.7 IPSW(약 3 GB) 다운로드 → 지우기 → 설치, 15–30분. 중간에 폰이 재부팅한다.
   - "나의 iPhone 찾기"가 켜져 있으면 Finder가 복원을 거부하며 끄라고 한다 → 사용자에게 넘긴다.
3. 끝나면 폰이 "안녕하세요" 화면으로 켜진다. 사용자와 함께 폰에서:
   - Apple ID 로그인 **건너뛰기**(iCloud 없음 → 각종 알림 최소화). 앱을 넣고 싶을 때만
     App Store에 로그인(iOS 12라 "마지막 호환 버전 다운로드"로 깔리는 앱이 많다).
   - 설정 > 스크린 타임 > 콘텐츠 및 개인정보 보호 제한: 앱 설치/삭제 금지, 앱 내 구입 금지,
     연령 등급 제한. 필요하면 설정 > 손쉬운 사용 > 사용법 유도(Guided Access)로 한 앱에 고정.
   - 설정 > 일반 > 소프트웨어 업데이트에 "최신 상태"로 나오면 완료.
4. 결과를 사용자에게 보고하고 이 파일을 `done/`으로 옮긴 뒤 commit·push.

## 하지 말 것
- Apple ID 암호·암호 입력 대행, 결제 정보 입력 금지.
- "나의 iPhone 찾기"가 켜진 상태에서 지우지 말 것(활성화 잠금).
- 백업 여부를 묻지 않고 지우지 말 것.
