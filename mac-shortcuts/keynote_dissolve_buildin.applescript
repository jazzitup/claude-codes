-- Keynote: 선택한 객체에 Animate > Build In > Dissolve 효과를 넣는다. (keynote_dissolve_buildin.sh 가 applet 으로 컴파일해 실행)
on notify(msg)
	display notification msg with title "Keynote: Dissolve build in"
end notify

on firstMatch(elems, labels)
	-- 이름 또는 설명이 labels 중 하나인 첫 UI 요소
	tell application "System Events"
		repeat with e in elems
			set nm to ""
			set ds to ""
			try
				set nm to name of e as string
			end try
			try
				set ds to description of e as string
			end try
			if (labels contains nm) or (labels contains ds) then return contents of e
		end repeat
	end tell
	return missing value
end firstMatch

try
	tell application "System Events"
		if not (exists process "Keynote") then
			my notify("Keynote가 실행 중이 아닙니다.")
			return "no keynote"
		end if
		tell process "Keynote"
			set frontmost to true
			if (count of windows) is 0 then
				my notify("열린 Keynote 문서가 없습니다.")
				return "no window"
			end if
			set w to window 1
			-- 1) Animate 인스펙터 탭
			set opened to false
			try
				set rb to my firstMatch(radio buttons of group 1 of toolbar 1 of w, {"Animate", "애니메이션"})
				if rb is not missing value then
					if (value of rb) is 0 then click rb
					set opened to true
				end if
			end try
			if not opened then
				-- 툴바가 숨겨진 경우: View > Inspector > (두 번째 항목 = Animate)
				click menu item 2 of menu 1 of menu item 4 of menu 1 of menu bar item 9 of menu bar 1
			end if
			delay 0.3
			set sg to splitter group 1 of w
			-- 2) Build In 세그먼트 (객체 미선택이면 세그먼트가 "Transitions" 하나뿐)
			set rg to radio group 1 of sg
			if (count of radio buttons of rg) < 2 then
				my notify("슬라이드에서 객체를 먼저 선택하세요.")
				return "nothing selected"
			end if
			set bi to my firstMatch(radio buttons of rg, {"Build In", "빌드 인", "나타나기"})
			if bi is missing value then set bi to radio button 1 of rg
			if (value of bi) is 0 then
				click bi
				delay 0.3
			end if
			-- 3) Add an Effect / Change 버튼
			set btn to my firstMatch(buttons of sg, {"Add an Effect", "Change", "효과 추가", "변경"})
			if btn is missing value then
				my notify("'Add an Effect' 버튼을 찾지 못했습니다.")
				return "no add-effect button: " & ((name of buttons of sg) as string)
			end if
			click btn
			-- 4) 팝오버에서 Dissolve
			set pop to missing value
			repeat 30 times
				if (exists (first UI element of btn whose role is "AXPopover")) then
					set pop to (first UI element of btn whose role is "AXPopover")
					exit repeat
				end if
				delay 0.1
			end repeat
			if pop is missing value then
				my notify("효과 팝오버가 열리지 않았습니다.")
				return "no popover"
			end if
			set target to my firstMatch(buttons of scroll area 1 of pop, {"Dissolve", "디졸브"})
			if target is missing value then
				key code 53 -- esc
				my notify("팝오버에서 Dissolve를 찾지 못했습니다.")
				return "no dissolve: " & ((name of buttons of scroll area 1 of pop) as string)
			end if
			click target
			return "ok"
		end tell
	end tell
on error errMsg number errNum
	if errNum is -25211 or errMsg contains "assistive" or errMsg contains "손쉬운" then
		display dialog "이 단축키는 손쉬운 사용(Accessibility) 권한이 필요합니다." & return & return & "시스템 설정 > 개인정보 보호 및 보안 > 손쉬운 사용에서 'Keynote Dissolve' 앱을 켜 주세요. (목록에 없으면 + 로 ~/Library/Application Support/claude-codes/Keynote Dissolve.app 추가)" buttons {"설정 열기", "확인"} default button 1 with icon caution
		if button returned of result is "설정 열기" then do shell script "open x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
	else
		my notify("오류: " & errMsg)
	end if
	return "error " & errNum & ": " & errMsg
end try
