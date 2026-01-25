# Comments Review Skill

## 목적
주석이 코드를 이해하는 데 도움이 되며, 특히 "왜(Why)"를 설명하는지 평가합니다.

## 핵심 원칙

> "주석은 코드가 무엇을 하는지보다 **왜 존재하는지** 설명해야 한다."

## Google의 규칙

```
코드가 이해 안 됨 → 주석 추가가 아닌, 코드를 더 명확하게 재작성
```

## 검토 기준

### 좋은 주석
| 유형 | 예시 | 설명 |
|------|------|------|
| **Why** | `# 레거시 API 호환을 위해 이 형식 유지` | 의사결정 배경 |
| **Warning** | `# 주의: 이 순서 변경 금지 (race condition)` | 함정 경고 |
| **TODO** | `# TODO: v2.0에서 deprecated 예정` | 향후 작업 |
| **Reference** | `# RFC 7231 Section 6.1 참조` | 외부 문서 링크 |

### 불필요한 주석
| 유형 | 예시 | 대안 |
|------|------|------|
| **What** | `# i를 1 증가시킴` | 코드로 명확 |
| **Obvious** | `# 사용자 가져오기 \n get_user()` | 삭제 |
| **Outdated** | `# DB에서 조회` (실제론 캐시 사용) | 업데이트 또는 삭제 |

## Red Flags (경고 신호)

- 📅 오래된 TODO (날짜 없는 TODO)
- 🔄 코드와 맞지 않는 주석
- 📖 코드 번역 수준의 주석
- 🚫 주석 처리된 코드
- 📝 과도한 docstring (내부 함수에 장황한 설명)

## 주석이 필요한 경우

### 1. 비직관적인 해결책
```python
# MySQL 5.7 버그 우회 - LIMIT과 함께 서브쿼리 사용 시
# 인덱스가 무시되는 문제 (Bug #12345)
query = "SELECT * FROM (SELECT * FROM users LIMIT 100) AS t WHERE ..."
```

### 2. 성능 최적화
```python
# 캐시 히트율 95% 이상이므로 매번 검사하는 것보다
# 실패 시 재시도가 더 효율적
result = cache.get(key) or db.query(key)
```

### 3. 외부 제약
```python
# 결제 게이트웨이 API가 동시 요청 5개 제한
semaphore = asyncio.Semaphore(5)
```

### 4. 임시 해결책
```python
# FIXME: 인증 서버 마이그레이션 완료 후 제거
# 현재 구/신 서버 동시 지원 필요
if use_legacy_auth():
    return legacy_authenticate(token)
```

## 질문 예시

```markdown
**[Minor]** src/services/payment.py:67

주석이 코드와 맞지 않습니다:
```python
# 할인 적용
total = price * 1.1  # 실제로는 10% 추가
```

주석을 업데이트하거나 삭제해주세요.
```

```markdown
Nit: src/utils/validator.py:23

```python
# 이메일 검증
def validate_email(email):
```

함수명이 충분히 명확하므로 이 주석은 불필요합니다.
```

```markdown
**[Minor]** src/core/engine.py:156

이 로직이 왜 필요한지 이해하기 어렵습니다.
코드를 더 명확하게 하거나, 배경을 설명하는 주석을 추가해주세요.
```

## TODO 주석 가이드

### 좋은 TODO
```python
# TODO(username, 2024-01): OAuth2 지원 추가
# TODO: Issue #123 - 메모리 누수 수정
```

### 나쁜 TODO
```python
# TODO: fix this
# TODO: 나중에 수정
# TODO (2019년...)  ← 방치됨
```

## DO / DON'T

### DO
- Why 설명이 필요한 복잡한 로직에 주석 요청
- 오래된/잘못된 주석 지적
- 코드 명확화를 주석 추가보다 우선 제안

### DON'T
- 모든 함수에 docstring 요구
- 자명한 코드에 주석 요구
- 개인 주석 스타일 강요
