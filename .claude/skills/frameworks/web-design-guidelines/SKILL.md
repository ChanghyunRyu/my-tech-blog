---
name: web-design-guidelines
description: Vercel Web Interface Guidelines - 100+ UI/UX 규칙. 접근성, 폼, 애니메이션, 타이포그래피, 성능, 다크모드, i18n. UI 코드 리뷰용.
source: https://github.com/vercel-labs/web-interface-guidelines
---

# Web Interface Guidelines

UI 코드 리뷰 시 아래 규칙들을 체크합니다. 간결하지만 포괄적으로 검토하세요.

---

## Accessibility

- Icon-only 버튼에 `aria-label` 필수
- Form controls에 `<label>` 또는 `aria-label` 필수
- Interactive elements에 키보드 핸들러 필수 (`onKeyDown`/`onKeyUp`)
- 액션은 `<button>`, 네비게이션은 `<a>`/`<Link>` (`<div onClick>` 금지)
- 이미지에 `alt` 필수 (장식용은 `alt=""`)
- 장식용 아이콘에 `aria-hidden="true"`
- 비동기 업데이트(토스트, 검증)에 `aria-live="polite"`
- ARIA보다 시맨틱 HTML 우선 (`<button>`, `<a>`, `<label>`, `<table>`)
- 헤딩은 `<h1>`–`<h6>` 계층적으로; main content 스킵 링크 포함
- 헤딩 앵커에 `scroll-margin-top`

---

## Focus States

- Interactive elements에 visible focus 필수: `focus-visible:ring-*` 또는 동등
- `outline-none` / `outline: none` 사용 시 대체 focus 필수
- `:focus`보다 `:focus-visible` 사용 (클릭 시 포커스 링 방지)
- Compound controls는 `:focus-within`으로 그룹 포커스

---

## Forms

- Input에 `autocomplete`와 의미 있는 `name` 필수
- 올바른 `type` 사용 (`email`, `tel`, `url`, `number`) 및 `inputmode`
- 붙여넣기 차단 금지 (`onPaste` + `preventDefault`)
- Label 클릭 가능 (`htmlFor` 또는 control 감싸기)
- 이메일, 코드, 사용자명에 `spellCheck={false}`
- Checkbox/Radio: label + control이 단일 hit target 공유 (dead zones 없음)
- Submit 버튼: 요청 시작까지 enabled, 요청 중 spinner
- 에러는 필드 옆에 inline; submit 시 첫 에러에 focus
- Placeholder는 `…`로 끝나고 예시 패턴 표시
- 비인증 필드에 `autocomplete="off"` (password manager 트리거 방지)
- 저장되지 않은 변경 시 네비게이션 경고 (`beforeunload` 또는 router guard)

---

## Animation

- `prefers-reduced-motion` 존중 (축소 버전 제공 또는 비활성화)
- `transform`/`opacity`만 애니메이션 (compositor 친화적)
- `transition: all` 금지 - 속성 명시적 나열
- 올바른 `transform-origin` 설정
- SVG: `<g>` wrapper에 `transform-box: fill-box; transform-origin: center`
- 애니메이션 중단 가능 - 애니메이션 중 사용자 입력에 응답

---

## Typography

- `...` 대신 `…` 사용
- 직선 따옴표 `"` 대신 둥근 따옴표 `"` `"` 사용
- Non-breaking spaces: `10&nbsp;MB`, `⌘&nbsp;K`, 브랜드명
- 로딩 상태는 `…`로 끝남: `"Loading…"`, `"Saving…"`
- 숫자 열/비교에 `font-variant-numeric: tabular-nums`
- 헤딩에 `text-wrap: balance` 또는 `text-pretty` (widow 방지)

---

## Content Handling

- 텍스트 컨테이너가 긴 콘텐츠 처리: `truncate`, `line-clamp-*`, 또는 `break-words`
- Flex children에 `min-w-0` (텍스트 truncation 허용)
- Empty states 처리 - 빈 string/array에 깨진 UI 렌더링 금지
- 사용자 생성 콘텐츠: 짧은/평균/매우 긴 입력 예상

---

## Images

- `<img>`에 명시적 `width`와 `height` 필수 (CLS 방지)
- Below-fold 이미지: `loading="lazy"`
- Above-fold critical 이미지: `priority` 또는 `fetchpriority="high"`

---

## Performance

- 대형 리스트 (>50 items): 가상화 (`virtua`, `content-visibility: auto`)
- 렌더 중 layout reads 금지 (`getBoundingClientRect`, `offsetHeight`, `offsetWidth`, `scrollTop`)
- DOM reads/writes 배치; interleaving 방지
- Uncontrolled inputs 선호; controlled inputs는 keystroke당 비용 저렴해야 함
- CDN/asset 도메인에 `<link rel="preconnect">` 추가
- Critical fonts: `<link rel="preload" as="font">`와 `font-display: swap`

---

## Navigation & State

- URL이 상태 반영 - 필터, 탭, 페이지네이션, 확장 패널은 query params에
- 링크는 `<a>`/`<Link>` 사용 (Cmd/Ctrl+click, middle-click 지원)
- 모든 stateful UI deep-link (`useState` 사용 시 nuqs 등으로 URL 동기화 고려)
- 파괴적 액션은 확인 모달 또는 undo 창 필요 - 즉시 실행 금지

---

## Touch & Interaction

- `touch-action: manipulation` (double-tap zoom 지연 방지)
- `-webkit-tap-highlight-color` 의도적 설정
- 모달/drawer/sheet에 `overscroll-behavior: contain`
- 드래그 중: 텍스트 선택 비활성화, 드래그된 요소에 `inert`
- `autoFocus` 절제 - 데스크톱만, 단일 primary input; 모바일 피함

---

## Safe Areas & Layout

- Full-bleed 레이아웃은 `env(safe-area-inset-*)` 필요 (노치 대응)
- 원치 않는 스크롤바 방지: 컨테이너에 `overflow-x-hidden`, 콘텐츠 overflow 수정
- JS 측정보다 Flex/grid 선호

---

## Dark Mode & Theming

- 다크 테마에 `color-scheme: dark` on `<html>` (스크롤바, 입력 수정)
- `<meta name="theme-color">`가 페이지 배경과 일치
- Native `<select>`: 명시적 `background-color`와 `color` (Windows 다크 모드)

---

## Locale & i18n

- 날짜/시간: 하드코딩 형식 대신 `Intl.DateTimeFormat` 사용
- 숫자/통화: 하드코딩 형식 대신 `Intl.NumberFormat` 사용
- IP 대신 `Accept-Language` / `navigator.languages`로 언어 감지

---

## Hydration Safety

- `value`가 있는 input은 `onChange` 필요 (또는 uncontrolled는 `defaultValue`)
- 날짜/시간 렌더링: hydration mismatch 방지 (서버 vs 클라이언트)
- `suppressHydrationWarning`은 정말 필요한 곳에만

---

## Hover & Interactive States

- 버튼/링크에 `hover:` 상태 필요 (시각적 피드백)
- Interactive states는 대비 증가: hover/active/focus가 rest보다 더 눈에 띔

---

## Content & Copy

- 능동태: "CLI를 설치하세요" not "CLI가 설치됩니다"
- 헤딩/버튼은 Title Case (Chicago 스타일)
- 숫자는 숫자로: "8 deployments" not "eight"
- 구체적인 버튼 레이블: "API Key 저장" not "계속"
- 에러 메시지는 수정 방법/다음 단계 포함, 문제만 X
- 2인칭 사용; 1인칭 피함
- 공간 제약 시 "and"보다 `&`

---

## Anti-patterns (이것들 플래그)

- `user-scalable=no` 또는 `maximum-scale=1` 줌 비활성화
- `onPaste`와 `preventDefault`
- `transition: all`
- focus-visible 대체 없이 `outline-none`
- `<a>` 없이 inline `onClick` 네비게이션
- click handler가 있는 `<div>` 또는 `<span>` (`<button>`이어야 함)
- dimensions 없는 이미지
- 가상화 없이 대형 배열 `.map()`
- label 없는 form inputs
- `aria-label` 없는 icon 버튼
- 하드코딩 날짜/숫자 형식 (`Intl.*` 사용)
- 명확한 정당화 없는 `autoFocus`

---

## Output Format

파일별로 그룹화. `file:line` 형식 (VS Code 클릭 가능). 간결한 발견.

```text
## src/Button.tsx

src/Button.tsx:42 - icon button missing aria-label
src/Button.tsx:18 - input lacks label
src/Button.tsx:55 - animation missing prefers-reduced-motion
src/Button.tsx:67 - transition: all → list properties

## src/Modal.tsx

src/Modal.tsx:12 - missing overscroll-behavior: contain
src/Modal.tsx:34 - "..." → "…"

## src/Card.tsx

✓ pass
```

이슈 + 위치 명시. 수정이 자명하지 않은 경우에만 설명. 서문 없음.
