# 토큰 압축 모드 (--uc / Ultra Concise)

응답을 최대한 간결하게 압축하여 토큰을 절약하는 모드입니다.

## 활성화

```
/explain --uc 코드
"이 함수 설명해줘 --uc"
```

## 동작 원칙

### 1. 최소 단어 사용

```markdown
## 일반 모드
이 함수는 사용자의 입력을 받아서 유효성을 검사하고,
유효한 경우 데이터베이스에 저장합니다. 만약 유효하지 않은
경우에는 에러 메시지를 반환합니다.

## --uc 모드
입력 검증 → 유효 시 DB 저장, 아니면 에러 반환
```

### 2. 불릿/숫자 선호

```markdown
## 일반 모드
먼저 사용자 인증을 확인합니다. 그 다음 권한을 검사하고,
요청된 리소스에 접근합니다. 마지막으로 결과를 반환합니다.

## --uc 모드
1. 인증
2. 권한 검사
3. 리소스 접근
4. 결과 반환
```

### 3. 약어/기호 사용

```markdown
## 약어 테이블

| 전체 | 약어 |
|------|------|
| function | fn |
| parameter | param |
| return | → |
| if/then | ? |
| implements | impl |
| configuration | cfg |
| database | DB |
| authentication | auth |
| authorization | authz |
| repository | repo |
| dependency | dep |
```

### 4. 코드 블록 압축

```markdown
## 일반 모드
```python
def get_user(user_id: int) -> Optional[User]:
    """
    사용자 ID로 사용자를 조회합니다.

    Args:
        user_id: 조회할 사용자 ID

    Returns:
        User 객체 또는 None
    """
    return self.repository.find_by_id(user_id)
```

## --uc 모드
`get_user(id) → User|None` - DB에서 id로 조회
```

## 출력 형식

### 코드 설명

```markdown
# fn: get_user

- in: id (int)
- out: User|None
- 동작: repo.find_by_id(id)
- 용도: 사용자 조회
```

### 에러 분석

```markdown
# 에러: NullPointer

- 위치: user.py:45
- 원인: user=None
- 수정: `if user:` 체크 추가
```

### 리뷰 결과

```markdown
# 리뷰: src/auth.py

✓ 구조, 네이밍
⚠️ 에러처리 부족 (L23)
✗ SQL 인젝션 (L45)

수정: L23 try/except, L45 파라미터화
```

### 비교 분석

```markdown
# A vs B

| 기준 | A | B |
|------|---|---|
| 성능 | ++ | + |
| 복잡도 | - | + |
| 유지보수 | + | ++ |

→ B 권장 (유지보수 중시 시)
```

## 압축 레벨

### Level 1: 경량 압축 (기본)
- 불필요한 수식어 제거
- 리스트 형식 선호
- 50% 토큰 절감

### Level 2: 중간 압축 (--uc)
- 약어 사용
- 코드 블록 최소화
- 70% 토큰 절감

### Level 3: 극한 압축 (--uc --max)
- 기호 중심
- 키워드만
- 90% 토큰 절감

## 변환 예시

### 에이전트 결과 요약

```markdown
## 일반

security-reviewer가 코드를 분석한 결과, 총 3개의 취약점이
발견되었습니다. 2개는 중간 심각도이고 1개는 낮은 심각도입니다.
주요 문제는 SQL 인젝션 가능성과 XSS 취약점입니다.
권장 조치로는 PreparedStatement 사용과 출력 이스케이프를
적용하는 것입니다.

## --uc

보안검사: 취약점 3개
- M: SQL인젝션 L45 → PreparedStatement
- M: XSS L67 → escape
- L: 약한암호 L12 → bcrypt
```

### 작업 계획

```markdown
## 일반

결제 시스템을 구현하기 위해 다음 단계를 진행합니다.
먼저 PG사 연동을 위한 API를 구현하고, 그 다음 결제
프로세스 흐름을 개발합니다. 이후 테스트를 작성하고
문서화를 진행합니다.

## --uc

결제 시스템:
1. PG API 구현
2. 결제 플로우
3. 테스트
4. 문서화
```

## 주의사항

- 핵심 정보는 절대 생략하지 않음
- 코드 스니펫은 필요 시 전체 표시
- 보안 관련 정보는 압축하지 않음
- 사용자가 이해 못하면 일반 모드로 전환
