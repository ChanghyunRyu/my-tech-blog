---
name: security
description: 보안 리뷰 수행. security-reviewer를 호출합니다.
agent: security-reviewer
---

# /security

보안 리뷰를 수행합니다.

## 사용법

```
/security                  # 최근 변경 보안 리뷰
/security src/auth/        # 특정 디렉토리
/security --deps           # 의존성 취약점 검사
/security --threat-model   # 위협 모델링 포함
```

## 동작

1. 범위 파악
2. 위협 모델링 (STRIDE)
3. OWASP Top 10 기반 정적 분석
4. 의존성 취약점 검사
5. 결과 작성

## 검토 항목 (OWASP Top 10 2025)

1. **A01 Access Control** - 권한 검증
2. **A03 Injection** - 입력 검증
3. **A07 Authentication** - 인증 안전성
4. **Dependencies** - 취약한 패키지
5. **Secrets** - 비밀값 노출
6. **Logging** - 민감 정보 로깅
7. **Error Handling** - 정보 노출

## 심각도

| 레벨 | 조치 |
|------|------|
| Critical | 즉시 수정 필수 |
| High | 릴리스 전 수정 |
| Medium | 수정 권장 |
| Low | 고려 |

## 출력

- `docs/reviews/security/YYYY-MM-DD-{target}.md`

## 옵션

| 플래그 | 효과 |
|--------|------|
| `--deps` | 의존성 취약점 중점 |
| `--threat-model` | 상세 위협 모델링 |
