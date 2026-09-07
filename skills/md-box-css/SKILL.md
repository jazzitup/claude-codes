---
name: md-box-css
description: >
  Turn unstyled semantic `<div class="...">` sections in a lecture-note
  markdown file (e.g. `histbox` "과학사 한 장면" boxes from the
  lecture-history-enrich skill, or `goalbox`/`exbox`/`solbox` from
  pennylane-codebook-notes) into visually bordered boxes, by adding a
  `<style>` block at the top of the .md file — Obsidian renders raw HTML
  including `<style>` tags inside notes, so this is enough with no plugin
  needed. Use when the user points at a specific kind of section in an
  existing lecture-note .md/.html and asks to "네모 쳐줘" / "박스로 만들어줘"
  / "박스 형태로 바꿔" / "테두리 넣어줘", especially when the classes are
  already present in the file but render as plain unstyled text because no
  CSS defines them. Korean triggers: 박스 쳐줘, 네모 박스로 만들어줘, 테두리
  넣어줘, 박스 형태로 바꿔줘, 이 부분 박스로.
---

# 마크다운 노트의 class 섹션을 박스로 만들기

`pennylane-codebook-notes`/`lecture-history-enrich` 계열 스킬이 만드는
강의노트는 `<div class="histbox">`, `<div class="goalbox">`,
`<div class="exbox">` 처럼 **의미 있는 class 이름은 붙어 있지만, 그 class를
실제로 꾸며주는 `<style>` 규칙은 따로 없는 경우**가 많다 — 특히 원래
HTML로 만들었던 노트를 나중에(예: `formula-latexify` 스킬로) `.md`로
변환하면서 `<head>`/`<style>` 블록이 통째로 빠지는 경우 (2026-09-07,
`Week02_Module2_single_qubit_gates_보강판.md`에서 실제로 이런 상태를
발견함 — `histbox`/`histportrait`/`histbody`/`histtitle` class는 5군데
다 있는데 `<style>` 자체가 파일에 하나도 없어서 그냥 밋밋한 텍스트로만
보였다). 이 스킬은 그 class들에 테두리 있는 박스 스타일을 붙여준다.

## 1. 어떤 class가 있는지, 이미 스타일이 있는지 확인한다

파일에 base64 이미지가 박혀 있으면 `Read`로 통째로 읽으면 토큰을
낭비하거나 바로 한도 초과가 난다 (`lecture-history-enrich`가 겪은 문제와
동일). 먼저 grep으로 구조만 훑는다.

```bash
grep -n '<style' "$FILE"                     # 이미 스타일 블록이 있는지
grep -n 'class="[a-zA-Z-]*box' "$FILE"        # ...box 계열 class들
grep -n 'class="hist' "$FILE"                 # histbox 계열이면 이렇게
```

`<style>`이 이미 있으면 그 안에 새 규칙을 추가하고, 없으면 2단계처럼
새로 만든다. `grep -c 'class="histbox"'`로 박스 개수를 세어두면, 나중에
수정 후 개수가 그대로인지(실수로 지운 게 없는지) 검증할 수 있다.

## 2. `<style>` 블록을 문서 맨 위(첫 heading 직후)에 추가한다

CSS는 문서 내 위치와 무관하게 전체에 적용되므로, 굳이 각 박스 바로 앞에
넣을 필요 없이 파일 맨 위(제목 다음, 첫 `<div>` 시작 전)에 한 번만
넣는 것이 깔끔하다. `Edit` 도구로 파일 맨 앞부분(제목 줄 + 그다음 줄)을
앵커로 삼아 그 사이에 `<style>...</style>`를 끼워 넣는다.

## 3. Obsidian 라이트/다크 테마 모두 대응하는 3중 정의 패턴을 쓴다

**주의**: 이건 Claude Artifact가 쓰는 `[data-theme="dark"]` 패턴과
다르다 — Obsidian은 실제 테마 전환 시 `<body>`에 `.theme-dark` /
`.theme-light` class를 붙인다. 셋을 다 정의해야 OS 설정과 Obsidian 앱
자체 토글이 어긋나는 경우까지 커버된다.

```css
.histbox {
  --hist-bg: #f6f3fb;      /* 기본(라이트) 값 */
  --hist-border: #d9cdf0;
  --hist-title: #5b3fa0;
  --hist-name: #6b6b6b;
  display: flex;
  gap: 18px;
  align-items: flex-start;
  border: 1.5px solid var(--hist-border);
  border-radius: 10px;
  background: var(--hist-bg);
  padding: 16px 20px;
  margin: 20px 0;
}
@media (prefers-color-scheme: dark) {
  .histbox { --hist-bg: #2a2438; --hist-border: #4a3d6b;
             --hist-title: #c9a9ff; --hist-name: #b8b0c8; }
}
.theme-dark .histbox {
  --hist-bg: #2a2438; --hist-border: #4a3d6b;
  --hist-title: #c9a9ff; --hist-name: #b8b0c8;
}
.theme-light .histbox {
  --hist-bg: #f6f3fb; --hist-border: #d9cdf0;
  --hist-title: #5b3fa0; --hist-name: #6b6b6b;
}
```

박스 안에 초상 사진 + 본문이 나란히(flex) 들어가는 구조(`histportrait`
+ `histbody`)라면, 좁은 화면(모바일)에서 세로로 쌓이도록
`@media (max-width: 480px) { .histbox { flex-direction: column; } }`도
넣는다. 초상이 2명 이상이면(`histportrait-group`) 그 안에서 다시
`display:flex; gap:10px;`로 나란히 배치한다.

## 4. 색상은 박스 종류별로 겹치지 않게 고른다

한 노트 안에 여러 종류의 박스가 있을 수 있으므로(목표=goalbox,
연습문제=exbox, 풀이=solbox, 역사=histbox 등), 이미 다른 색을 쓰고 있는
class와 겹치지 않는 새 색을 고른다. 2026-09-07에 histbox는 보라 계열
(`#5b3fa0` 라이트 / `#c9a9ff` 다크)을 썼다. 예시 배정:

| class | 색 계열 | 쓰임 |
|---|---|---|
| `goalbox` | 파랑 | "What will you learn?" 목표 |
| `exbox` | 주황 | 연습문제 |
| `solbox` | 초록 | 풀이 |
| `histbox` | 보라 | 과학사 에피소드 |

## 5. 검증

```bash
grep -c 'class="histbox"' "$FILE"    # 수정 전과 개수 같은지
grep -n '<style>\|</style>' "$FILE"  # 태그 짝이 맞는지 (여는/닫는 각 1개)
```

가능하면 Obsidian에서 실제로 열어 라이트/다크 모드를 둘 다 토글해보고
박스 테두리·배경이 잘 바뀌는지 눈으로 확인한다.

## 알아둘 것

- 이 노트들은 원래 `pennylane-codebook-notes` 스킬이 Google Docs
  붙여넣기용 HTML로 만들 때 `templates/style_block.txt`를 `<head>`에
  넣는 걸 전제로 class 이름들(`subtitle`, `meta`, `toc`, `goalbox`,
  `formula`, `figure`, `exbox`, `solbox`, `num`, `divider`,
  `table.summary`)을 붙인다. `.md`로 변환되면서 그 style block이
  통째로 사라지므로, 다른 class들(`goalbox` 등)도 같은 증상(박스로 안
  보임)일 가능성이 높다 — 사용자가 특정 박스만 짚어서 요청했다면 그
  범위만 고치고, 문서 전체를 다 손대지 않는다(요청 범위를 벗어나지
  않기).
- base64 이미지가 박힌 큰 파일은 `Read`로 전체를 읽지 말고, 먼저
  `sed -E 's#(data:image/[a-zA-Z]+;base64,)[A-Za-z0-9+/=]+#\1TRUNCATED#g'`
  로 트렁케이션한 사본을 스크래치패드에 만들어 구조 파악에 쓴다
  (`lecture-history-enrich` 스킬과 동일한 요령).
