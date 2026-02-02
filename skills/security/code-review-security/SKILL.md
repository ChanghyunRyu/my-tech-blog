# Security Quick Check Skill

## 목적
코드 리뷰 시 빠르게 확인할 수 있는 보안 체크리스트입니다.
심층 보안 분석은 `security-reviewer` 에이전트를 사용하세요.

## 빠른 체크리스트 (6개 항목)

| 체크 | 항목 | 심각도 | 검색 키워드 |
|------|------|--------|-------------|
| [ ] | 사용자 입력이 검증/이스케이프됨 | High | `request`, `req.body`, `input` |
| [ ] | SQL 쿼리가 파라미터화됨 | Critical | `execute`, `query`, `cursor` |
| [ ] | 민감 데이터가 로그에 노출 안됨 | High | `logger`, `console.log`, `print` |
| [ ] | 하드코딩된 비밀값 없음 | Critical | `password`, `secret`, `api_key` |
| [ ] | 권한 검사 존재 | High | `authorize`, `permission`, `role` |
| [ ] | 에러 메시지에 내부 정보 노출 없음 | Medium | `catch`, `except`, `error` |

## 빠른 스캔 패턴

### 즉시 보고해야 할 패턴

```python
# 하드코딩된 비밀 [Critical]
API_KEY = "sk-1234..."
PASSWORD = "admin123"
SECRET_KEY = "mysecret"

# SQL 인젝션 [Critical]
f"SELECT * FROM users WHERE id = {user_id}"
"SELECT * FROM users WHERE id = " + user_id

# 민감 정보 로깅 [High]
logger.info(f"Password: {password}")
print(f"Token: {token}")
```

### 주의 깊게 봐야 할 패턴

```python
# 사용자 입력 직접 사용
user_input = request.get_json()
os.system(user_input['command'])  # Command Injection

# 권한 검사 없는 엔드포인트
@app.route('/admin/users')
def list_users():  # 인증/권한 미들웨어 없음
    return get_all_users()

# 에러 상세 정보 노출
except Exception as e:
    return {"error": str(e), "trace": traceback.format_exc()}
```

## 심층 분석 트리거

다음 경우 `security-reviewer` 에이전트 호출 권장:

| 트리거 | 이유 |
|--------|------|
| 인증/권한 로직 변경 | 접근 제어 결함 가능성 |
| 암호화/해싱 관련 코드 | 암호화 구현 오류 가능성 |
| 외부 입력 처리 (API, 파일 업로드) | 인젝션 공격 가능성 |
| 결제/금융 관련 코드 | 비즈니스 로직 취약점 |
| 새로운 엔드포인트 추가 | 보안 검토 필요 |
| 의존성 변경 | 취약점 도입 가능성 |

## 코드 리뷰 시 질문

1. 이 코드에 사용자 입력이 들어오는가?
2. 그 입력이 어디로 전달되는가? (DB, 파일, 명령어, HTML)
3. 중간에 검증/이스케이프 단계가 있는가?
4. 이 작업에 권한 검사가 필요한가?
5. 에러 시 어떤 정보가 반환되는가?

## 보고 형식

```markdown
**[Security - High]** src/api/users.py:45

민감 정보 로깅: 비밀번호가 로그에 기록됩니다.

```python
logger.info(f"Login attempt: {username}, {password}")  # password 노출
```

**수정 제안**:
```python
logger.info(f"Login attempt: {username}")
```

> 심층 분석이 필요하면 `security-reviewer` 에이전트를 호출하세요.
```

## DO / DON'T

### DO
- 모든 사용자 입력 경로 추적
- 비밀 값 관련 코드 집중 검토
- 에러 핸들링 코드 확인

### DON'T
- 보안 이슈를 "나중에 고치자"고 넘기기
- 내부 시스템이라고 보안 검토 생략
- 프레임워크가 알아서 해줄 거라고 가정
