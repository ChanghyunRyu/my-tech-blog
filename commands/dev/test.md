---
name: test
description: 테스트 생성 및 실행. testing-orchestrator를 호출합니다.
agent: testing-orchestrator
---

# /test

테스트를 생성하거나 실행합니다.

## 사용법

```
/test                      # 전체 테스트 생성
/test src/auth/            # 특정 디렉토리
/test --run                # 테스트 실행
/test --e2e login          # E2E 테스트
```

## 동작

1. testing-orchestrator 호출
2. 언어/프레임워크 자동 감지
3. 테스트 전략 수립 (사용자 승인)
4. 테스트 코드 생성
5. 실행 및 리포트

## 옵션

| 플래그 | 효과 |
|--------|------|
| `--run` | 기존 테스트 실행만 |
| `--e2e` | E2E 테스트 중심 |
| `--coverage` | 커버리지 목표 설정 |

## 지원 프레임워크

| 언어 | 단위/API | E2E |
|------|---------|-----|
| Python | pytest + httpx | Playwright |
| Node.js | Vitest/Jest | Playwright |

## 출력

- `tests/` - 테스트 코드
- `e2e/` - E2E 테스트
- `docs/testing/` - 테스트 문서
