---
name: debug
description: 체계적 디버깅 세션 시작. systematic-debugging 스킬을 활용합니다.
skill: practices/systematic-debugging
---

# /debug

체계적인 디버깅 세션을 시작합니다.

## 사용법

```
/debug "TypeError: Cannot read property 'x' of undefined"
/debug --trace src/api/users.py:45
/debug --hypothesis "캐시 만료 문제"
```

## 동작

1. 문제 정의 및 재현 조건 확인
2. 가설 수립
3. 체계적 검증
4. 근본 원인 식별
5. 해결책 제안

## 디버깅 프로세스

```
문제 발생
    ↓
증상 수집 (에러 메시지, 스택트레이스)
    ↓
가설 생성 (가능한 원인들)
    ↓
가설 검증 (로그, 테스트, 코드 분석)
    ↓
근본 원인 확인
    ↓
해결책 제안 및 적용
```

## 옵션

| 플래그 | 효과 |
|--------|------|
| `--trace` | 특정 위치부터 추적 |
| `--hypothesis` | 특정 가설로 시작 |
| `--introspect` | 추론 과정 상세 설명 |

## 스킬 참조

- `.claude/skills/practices/systematic-debugging/`
