---
name: clone
description: 웹사이트 클론/프론트엔드 구현. frontend-orchestrator를 호출합니다.
agent: frontend-orchestrator
---

# /clone

웹사이트를 클론하거나 프론트엔드를 구현합니다.

## 사용법

```
/clone https://example.com     # URL로 클론
/clone --image design.png      # 이미지로 구현
/clone "미니멀한 블로그"        # 추상적 요청
```

## 동작

1. 요청 분류 (URL/이미지/추상적)
2. 스크래핑 또는 분석
3. 디자인 시스템 추출
4. 설계 (사용자 승인)
5. 구현
6. 검토 및 반복

## 7단계 워크플로우

```
Phase 0: 요청 분류 & 준비
    ↓
Phase 1: 스크래핑 (URL인 경우)
    ↓
Phase 2: 분석 → design-system.json
    ↓
Phase 3: 설계 → architecture.md [사용자 승인]
    ↓
Phase 4: 구현 → 컴포넌트 & 스타일
    ↓
Phase 5: 검토 → 픽셀 레벨 비교
    ↓
Phase 6: 수정 (필요 시, 최대 3회)
    ↓
Phase 7: 완료
```

## 출력

```
blog/src/
├── components/
├── styles/
└── pages/

docs/frontend/
├── design-system.json
├── architecture.md
└── review-report.md
```

## 옵션

| 플래그 | 효과 |
|--------|------|
| `--image` | 이미지 기반 구현 |
| `--framework` | 프레임워크 지정 (react/vue) |
| `--responsive` | 반응형 강조 |
