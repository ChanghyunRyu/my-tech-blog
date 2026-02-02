---
name: implement
description: 기능 구현 시작. 요구사항을 분석하고 단계별로 구현합니다.
---

# /implement

기능 구현을 시작합니다.

## 사용법

```
/implement 사용자 인증 기능
/implement --brainstorm 결제 시스템
/implement --task-manage 대시보드 구현
```

## 동작

1. 요구사항 분석
2. 구현 계획 수립 (--task-manage 시 상세 분해)
3. 단계별 구현
4. 테스트 제안

## 옵션

| 플래그 | 효과 |
|--------|------|
| `--brainstorm` | 여러 구현 방식 제안 후 선택 |
| `--task-manage` | 계층적 작업 분해 및 추적 |
| `--introspect` | 각 결정의 근거 명시 |

## 연관 커맨드

- `/design` - 먼저 설계가 필요한 경우
- `/test` - 구현 후 테스트
- `/review` - 구현 후 코드 리뷰
