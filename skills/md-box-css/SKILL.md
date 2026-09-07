---
name: md-box-css
description: >
  Turn unstyled semantic `<div class="...">` sections in a lecture-note
  markdown file (e.g. `histbox` "과학사 한 장면" boxes from the
  lecture-history-enrich skill, or `goalbox`/`exbox`/`solbox` from
  pennylane-codebook-notes) into visually bordered boxes, via an Obsidian
  CSS snippet placed in `<vault>/.obsidian/snippets/` and enabled in
  `appearance.json` — NOT an inline `<style>` tag in the note itself
  (Obsidian's Reading View strips those, confirmed 2026-09-07 when that
  approach silently did nothing). Use when the user points at a specific
  kind of section in an
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

## 2. 먼저 div 구조 자체가 "한 덩어리 HTML 블록"인지 확인한다 — 아니면 CSS를 붙여도 소용없다

⚠️ **가장 중요한 함정 (2026-09-07에 실제로 겪음)**: CSS 스니펫을 켰는데도
박스가 안 보이고, 위쪽에 **텅 빈 색깔 박스 하나**만 뜨고 그 아래로 사진·
이름·본문이 스타일 하나도 없이 줄줄이 흘러나오는 증상이 나면 — CSS
문제가 아니라 **HTML이 여러 조각으로 쪼개져서 렌더링된 것**이다.

CommonMark(Obsidian 포함 대부분의 마크다운 렌더러)의 HTML 블록 규칙은:
*여는 태그로 시작한 줄 다음에 빈 줄이 오면, 그 HTML 블록은 거기서
끝난다.* `pennylane-codebook-notes` 계열 노트는 아래처럼 각 div를
빈 줄로 감싸는 관습을 쓰는데,

```
<div class="histbox">

<div class="histportrait">

![이름](data:image/jpeg;base64,...)
...
</div>

</div>
```

이건 pandoc 같은 도구에서는 "빈 줄 다음엔 마크다운을 이어서 파싱하고,
짝 맞는 `</div>`를 만나면 다시 합친다"는 확장 문법으로 잘 동작하지만,
Obsidian의 렌더러는 그렇게 관대하지 않다. 실제로는 `<div class="histbox">`
바로 뒤의 빈 줄에서 그 블록이 즉시(내용 없이) 끝나버리고, 이어지는
`<div class="histportrait">`, `![이미지]()`, `<div class="name">`,
`</div>` 들이 전부 **따로따로** 파싱된다 — 그 결과 스타일이 걸린
`histbox`는 자식이 하나도 없는 빈 상자로, 나머지는 그냥 평범한 문단으로
렌더링된다. 스크린샷으로 이 증상을 정확히 확인할 수 있다: 위쪽에 빈
보라색 상자, 그 아래 스타일 없는 사진+텍스트.

**해결책: 그 div 블록 전체를 빈 줄 없이 한 줄(또는 최소한 빈 줄이
전혀 없는 연속된 여러 줄)로 압축**해서, 파서가 처음부터 끝까지 하나의
HTML 블록으로 인식하게 만든다. 이 경우 블록 내부는 더 이상 마크다운으로
처리되지 않으므로, 안에 있던 마크다운 문법도 같이 HTML로 바꿔줘야 한다:

- `![이름](data:image/...;base64,XXXX)` → `<img src="data:image/...;base64,XXXX" alt="이름">`
- `이름\` + 줄바꿈 + `(연도)` (마크다운 줄바꿈) → `이름<br>(연도)`
- 빈 줄로 나뉜 본문 문단들 → 문단마다 `<p>...</p>`로 감싸기
- `*기울임*` → `<em>기울임</em>` (본문 안에 게이트 이름 등을 이탤릭으로
  쓴 경우가 많으므로 빠뜨리지 않는다)
- `**굵게**`가 있다면 `<strong>굵게</strong>`로

파일에 base64 이미지가 많아 손으로 편집하기 어려우므로, **Python
정규식으로 각 박스의 구조를 통째로 매칭해서 재조립**하는 게 안전하다
(base64 문자열 자체는 캡처 그룹으로만 다루고 절대 다시 타이핑하지
않는다):

```python
import re

single_pat = re.compile(
    r'<div class="histbox">\n\n'
    r'<div class="histportrait">\n\n'
    r'!\[([^\]]+)\]\(data:image/jpeg;base64,([A-Za-z0-9+/=]+)\)\n\n'
    r'<div class="name">\n\n([^\\\n]+)\\\n\(([^)]+)\)\n\n</div>\n\n</div>\n\n'
    r'<div class="histbody">\n\n<div class="histtitle">\n\n([^\n]+)\n\n</div>\n\n'
    r'(.*?)\n\n</div>\n\n</div>',
    re.DOTALL,
)

def repl(m):
    alt, b64, name, years, title, body = m.groups()
    paras = "".join(f"<p>{p.strip()}</p>" for p in body.strip().split("\n\n") if p.strip())
    return (f'<div class="histbox"><div class="histportrait">'
            f'<img src="data:image/jpeg;base64,{b64}" alt="{alt}">'
            f'<div class="name">{name}<br>({years})</div></div>'
            f'<div class="histbody"><div class="histtitle">{title}</div>{paras}</div></div>')

text = re.sub(single_pat, repl, text)
```

여러 초상(`histportrait-group`)이 있는 박스는 패턴을 하나 더 만들어야
한다(포틀레이트 블록을 두 번 반복). **먼저 스크래치패드의 임시 파일에
써서 결과를 검증**(치환 전/후 `class="histbox"` 개수가 같은지,
`<div>`/`</div>` 개수가 정확히 같은지, `diff`로 박스 구간 밖은 전혀
안 바뀌었는지)하고 나서 실제 파일에 적용한다.

## 3. 노트 안에 `<style>` 태그를 직접 넣지 않는다 — Obsidian CSS 스니펫을 쓴다

⚠️ **2026-09-07에 실제로 틀렸던 접근**: 처음엔 `.md` 파일 맨 위에
`<style>...</style>` 블록을 그냥 끼워 넣었는데, Obsidian Reading
View가 노트 본문 안의 `<style>` 태그를 렌더링에 반영하지 않아서
(보안 목적의 새니타이징으로 보임) 사용자가 열어봐도 "그대론데?"였다.
**노트 파일 자체를 건드리는 대신, vault의 CSS 스니펫 기능을 쓴다**:

1. `<vault>/.obsidian/snippets/` 폴더가 없으면 만든다.
2. 그 안에 `<snippet이름>.css` 파일로 CSS 규칙만 순수하게 저장한다
   (`<style>` 태그 없이, 파일 전체가 곧 CSS).
3. `<vault>/.obsidian/appearance.json`의 `"enabledCssSnippets"` 배열에
   그 스니펫 이름(확장자 `.css` 제외)을 추가해서 활성화한다. 이 파일이
   비어있으면(`{}`) 아래처럼 새로 채운다:
   ```json
   { "enabledCssSnippets": ["histbox"] }
   ```
   이미 다른 스니펫이 활성화돼 있으면 배열에 이름만 추가한다(기존
   항목을 지우지 않는다).
4. 사용자에게 **Obsidian을 다시 열거나(reload), 설정 → 모양(Appearance)
   → CSS 스니펫에서 토글이 켜져 있는지 확인**하라고 안내한다 — 앱이
   켜져 있는 동안 파일을 직접 고쳤으므로 앱이 그 변경을 바로 감지하지
   못할 수 있다.

노트 `.md` 파일 자체는 건드릴 필요가 없다(class 이름은 이미 있으므로).
단, 이 노트가 나중에 `pennylane-codebook-notes` 파이프라인으로 진짜
HTML(`<head>`+`<style>`)로도 만들어질 수 있다면, 그때를 대비해 노트
안에도 동일한 CSS를 `<style>` 블록으로 남겨두는 것 자체는 무해하다 —
다만 **Obsidian에서 박스가 보이게 하는 실제 메커니즘은 항상 CSS
스니펫이라는 것**을 잊지 않는다.

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
grep -c 'class="histbox"' "$FILE"                      # 수정 전과 개수 같은지
cat "$VAULT/.obsidian/appearance.json"                 # 스니펫이 enabledCssSnippets에 들어갔는지
ls "$VAULT/.obsidian/snippets/"                        # css 파일이 실제로 생겼는지
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
