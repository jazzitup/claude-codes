---
name: capcut-project-sync
description: CapCut 데스크톱(맥) 편집 프로젝트(draft)를 Dropbox에 올려 두고, 다른 Mac(랩톱 등)에서 "불러와"라고 하면 그 Mac의 CapCut에 똑같이 열리게 설치한다. 원본 영상·음악은 이미 Dropbox에 있다고 가정하고, draft 폴더와 draft가 참조하는 CapCut 공용 파일(효과 캐시·프리셋·녹음)만 담는다. 경로는 그 Mac 기준으로 자동 변환. '캡컷 프로젝트 드롭박스에 올려줘', '편집 내용 저장해 둬', '불러와', '캡컷 프로젝트 불러와', '랩톱에서 이어서 편집' 요청 시 사용.
---

# CapCut 프로젝트 Dropbox 동기화

스크립트: `~/.claude/skills/capcut-project-sync/scripts/capcut_sync.py`
패키지 위치(기본): `<Dropbox>/K 고분 헌터스/_CapCut 편집 프로젝트/<draft이름>/`
(`CAPCUT_PKG_DIR` 환경변수로 Dropbox 루트 기준 상대경로 변경 가능)

CapCut draft 위치: `~/Movies/CapCut/User Data/Projects/com.lveditor.draft/<draft이름>/`
— `draft_info.json`(평문 JSON)에 미디어 절대경로가 들어 있고, `root_meta_info.json`이
CapCut 홈 화면의 프로젝트 목록이다.

## 올리기 (편집한 Mac에서: "드롭박스에 올려줘")

1. 어떤 draft인지 확인: 위 폴더에서 가장 최근 수정된 것, 또는 사용자가 말한 이름.
2. CapCut을 종료(Cmd+Q)하라고 안내하거나 `pgrep -x CapCut`으로 확인 — 열려 있으면 저장 안 된 편집이 빠질 수 있다.
3. `python3 $SK/capcut_sync.py push "<draft이름>"`
   - `Resources/audioAlg`(오디오 분석 캐시, 수 GB, draft_info가 참조하지 않음)는 뺀다.
   - draft 밖 참조 파일(Cache/effect, Cache/artistEffect, Presets/Combination, 다른 draft의 녹음 등)은
     `userdata_extra/`에 같은 상대경로로 담는다.
   - 원본 영상·음악이 Dropbox 밖(예: Downloads)에 있으면 경고하고 Dropbox로 옮길지 사용자에게 묻는다
     (`grep -o '"path":"[^"]*"' draft_info.json`으로 확인).

## 불러오기 (다른 Mac에서: "불러와")

1. `python3 $SK/capcut_sync.py list`로 Dropbox 패키지 목록 → 가장 최근 것(또는 사용자가 말한 것).
2. Dropbox가 패키지와 원본 영상을 다 받았는지 확인(파일이 '온라인 전용'이면 받아지는 동안 기다림).
3. CapCut 완전 종료 확인(`pgrep -x CapCut`; 실행 중이면 스크립트가 거부 — CapCut이 종료할 때
   root_meta_info.json을 덮어쓰기 때문).
4. `python3 $SK/capcut_sync.py pull "<draft이름>"`
   - 같은 이름 draft가 있으면 `.bak-<시각>`으로 옮겨 둔 뒤 복사.
   - 홈/Dropbox 경로가 다르면 모든 json 안의 절대경로를 이 Mac 기준으로 바꾼다.
   - root_meta_info.json 맨 앞에 등록(백업 `root_meta_info.json.bak-sync`).
   - 끝에 아직 없는 미디어 목록을 출력 → 있으면 Dropbox 동기화 대기 안내.
5. `open -a CapCut` → 홈 화면 첫 번째 프로젝트로 열린다. 사용자에게 열어서 타임라인 확인을 부탁.

## 주의

- 양쪽에서 동시에 편집하지 않는다. 다른 Mac에서 고친 뒤엔 그 Mac에서 다시 "올려줘" → 원래 Mac에서 "불러와".
- 유료 효과·폰트는 같은 CapCut 계정으로 로그인돼 있어야 정상 표시된다. 캐시에 없던 효과는 CapCut이 온라인에서 다시 받는다.
- 2026-11-19 첫 push 기준 패키지 크기 약 0.6GB(원본 영상 제외).
