---
name: react-best-practices
description: Vercel Engineering의 React/Next.js 성능 최적화 가이드. 50+ 규칙, 8개 카테고리. 개별 규칙은 rules/ 폴더 참조.
source: https://github.com/vercel-labs/agent-skills
---

# React Best Practices

**Version 1.0.0** | Vercel Engineering | January 2026

React/Next.js 성능 최적화 가이드. 50+ 규칙을 우선순위별로 정리.

## 규칙 카테고리

개별 규칙은 `rules/` 폴더에서 확인:

### 1. Eliminating Waterfalls — **CRITICAL**
- `async-defer-await.md` - await를 필요한 분기에서만 사용
- `async-parallel.md` - Promise.all()로 병렬 실행
- `async-suspense-boundaries.md` - 전략적 Suspense 배치
- `async-api-routes.md` - API 라우트 워터폴 방지
- `async-dependencies.md` - 의존성 기반 병렬화

### 2. Bundle Size Optimization — **CRITICAL**
- `bundle-barrel-imports.md` - Barrel 파일 import 회피
- `bundle-dynamic-imports.md` - 무거운 컴포넌트 동적 로드
- `bundle-defer-third-party.md` - 서드파티 라이브러리 지연 로드
- `bundle-conditional.md` - 조건부 모듈 로딩
- `bundle-preload.md` - 사용자 의도 기반 프리로드

### 3. Server-Side Performance — **HIGH**
- `server-auth-actions.md` - Server Action 인증 필수
- `server-serialization.md` - RSC 경계 직렬화 최소화
- `server-cache-react.md` - React.cache() 요청 중복 제거
- `server-cache-lru.md` - 크로스 요청 LRU 캐싱
- `server-parallel-fetching.md` - 컴포넌트 구성으로 병렬 fetch
- `server-dedup-props.md` - RSC props 중복 직렬화 방지
- `server-after-nonblocking.md` - after()로 비차단 작업

### 4. Client-Side Data Fetching — **MEDIUM-HIGH**
- `client-swr-dedup.md` - SWR 자동 중복 제거
- `client-event-listeners.md` - 전역 이벤트 리스너 중복 제거
- `client-passive-event-listeners.md` - passive 이벤트 리스너
- `client-localstorage-schema.md` - localStorage 버전 관리

### 5. Re-render Optimization — **MEDIUM**
- `rerender-functional-setstate.md` - 함수형 setState
- `rerender-lazy-state-init.md` - 지연 상태 초기화
- `rerender-transitions.md` - 비긴급 업데이트에 transition
- `rerender-memo.md` - 메모이제이션 컴포넌트 추출
- `rerender-defer-reads.md` - 상태 읽기 지연
- `rerender-dependencies.md` - effect 의존성 좁히기
- `rerender-derived-state.md` - 파생 상태 구독

### 6. Rendering Performance — **MEDIUM**
- `rendering-content-visibility.md` - CSS content-visibility
- `rendering-hydration-no-flicker.md` - hydration 깜빡임 방지
- `rendering-conditional-render.md` - 명시적 조건부 렌더링
- `rendering-hoist-jsx.md` - 정적 JSX 호이스팅
- `rendering-activity.md` - Activity 컴포넌트 사용
- `rendering-animate-svg-wrapper.md` - SVG 래퍼 애니메이션
- `rendering-svg-precision.md` - SVG 정밀도 최적화

### 7. JavaScript Performance — **LOW-MEDIUM**
- `js-index-maps.md` - 반복 조회에 Map 사용
- `js-tosorted-immutable.md` - toSorted() 불변성
- `js-cache-storage.md` - Storage API 캐싱
- `js-cache-function-results.md` - 함수 결과 캐싱
- `js-cache-property-access.md` - 속성 접근 캐싱
- `js-combine-iterations.md` - 배열 반복 결합
- `js-batch-dom-css.md` - DOM CSS 변경 배치
- `js-early-exit.md` - 조기 반환
- `js-length-check-first.md` - 길이 체크 우선
- `js-hoist-regexp.md` - RegExp 호이스팅
- `js-min-max-loop.md` - min/max 루프 사용
- `js-set-map-lookups.md` - Set/Map O(1) 조회

### 8. Advanced Patterns — **LOW**
- `advanced-use-latest.md` - useLatest 안정 콜백
- `advanced-event-handler-refs.md` - 이벤트 핸들러 refs

## 참조

- https://react.dev
- https://nextjs.org
- https://swr.vercel.app
- https://vercel.com/blog/how-we-optimized-package-imports-in-next-js
