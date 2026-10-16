#!/bin/bash
# Control+Option+Command+S: Schwartz QFT PDF 두 개(원본 + copy)를 Preview로 열어 배치한다.
#   모니터 2대 이상: 원본 = 가장 왼쪽 모니터 전체, copy = 가장 오른쪽 모니터의 왼쪽 절반
#   모니터 1대:      원본 하나만 열어 화면 전체
D="$HOME/Library/CloudStorage/Dropbox/Books and lectures"
NA="Schwartz Quantum_Field_Theory_and_the_Standard_Model_by_Schwartz_M.D._z-lib.org.pdf"
NB="Schwartz Quantum_Field_Theory_and_the_Standard_Model_by_Schwartz_M.D._z-lib.org copy.pdf"
/usr/bin/osascript -l JavaScript - "$D/$NA" "$D/$NB" <<'JXA'
ObjC.import('AppKit');
function run(argv) {
  const pA = argv[0], pB = argv[1];
  const nA = pA.split('/').pop(), nB = pB.split('/').pop();
  // 화면 좌표(Cocoa, 좌하단 원점) -> AppleScript bounds(주 화면 좌상단 원점)
  const scr = ObjC.unwrap($.NSScreen.screens).map(s => s.visibleFrame);
  const mainH = $.NSScreen.screens.objectAtIndex(0).frame.size.height;
  const box = f => [f.origin.x, mainH - (f.origin.y + f.size.height),
                    f.origin.x + f.size.width, mainH - f.origin.y].map(Math.round);
  scr.sort((a, b) => a.origin.x - b.origin.x);
  let bA, bB;
  if (scr.length >= 2) {
    bA = box(scr[0]);
    const r = box(scr[scr.length - 1]);
    bB = [r[0], r[1], Math.round((r[0] + r[2]) / 2), r[3]];
  } else {
    bA = box(scr[0]); bB = null;   // 한 개만 열어 전체화면
  }
  const P = Application('Preview');
  P.activate();
  P.open(Path(pA)); if (bB) P.open(Path(pB));
  const win = n => P.windows().find(w => w.name().startsWith(n));
  for (let i = 0; i < 40 && !(win(nA) && (!bB || win(nB))); i++) delay(0.25);
  const set = (w, b) => { if (w) w.bounds = {x: b[0], y: b[1], width: b[2] - b[0], height: b[3] - b[1]}; };
  set(win(nA), bA); if (bB) set(win(nB), bB);
}
JXA
