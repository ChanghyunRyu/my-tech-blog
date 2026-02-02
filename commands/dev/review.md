---
name: review
description: 코드 리뷰 수행. code-reviewer를 호출합니다.
agent: code-reviewer
---

# /review

코드 리뷰를 수행합니다.

## 사용법

```
/review                    # 최근 변경 리뷰
/review HEAD~3             # 최근 3개 커밋
/review src/auth/          # 특정 디렉토리
/review --security         # 보안 중점 리뷰
```

## 동작

1. 변경 범위 파악
2. code-reviewer 호출 (12가지 항목)
3. 결과를 docs/reviews/에 저장

## 검토 항목

1. Design - 구조적 적합성
2. Functionality - 의도대로 동작
3. Complexity - 단순화 가능성
4. Tests - 테스트 충분성
5. Naming - 명명 명확성
6. Comments - Why 설명
7. Style - 스타일 가이드
8. Consistency - 일관성
9. Documentation - 문서 업데이트
10. Every Line - 모든 라인 이해
11. Security - 보안 취약점
12. Performance - 성능 문제

## 옵션

| 플래그 | 효과 |
|--------|------|
| `--security` | 보안 관점 강화 (security-reviewer 연계) |
| `--performance` | 성능 분석 강화 |

## 출력

- `docs/reviews/YYYY-MM-DD-{target}.md`
