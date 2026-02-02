# Injection Review Skill

## 목적
SQL, NoSQL, OS 명령어, LDAP, XPath 인젝션 등 주입 취약점을 탐지합니다.

## OWASP A03:2025 - Injection

사용자 제공 데이터가 적절한 검증, 필터링, 이스케이프 없이 인터프리터에 전달될 때 발생합니다.

## 체크리스트

| 체크 | 항목 | 심각도 |
|------|------|--------|
| [ ] | SQL 쿼리가 파라미터화됨 (PreparedStatement) | Critical |
| [ ] | 사용자 입력이 이스케이프/검증됨 | Critical |
| [ ] | OS 명령 실행 시 입력 검증 | Critical |
| [ ] | NoSQL 쿼리 인젝션 방지 | High |
| [ ] | XSS 방지 (HTML 이스케이프) | High |
| [ ] | 경로 순회 (Path Traversal) 방지 | High |
| [ ] | 템플릿 인젝션 (SSTI) 방지 | High |

## Red Flags (경고 신호)

- 문자열 연결로 구성된 SQL 쿼리
- `eval()`, `exec()` 사용자 입력과 함께 사용
- `subprocess.call()` 또는 `os.system()` 사용자 입력 포함
- f-string 또는 format()으로 SQL 구성
- `innerHTML` 또는 `dangerouslySetInnerHTML` 사용

## 언어별 검토 패턴

### Python

```python
# 위험 패턴 - SQL Injection
query = f"SELECT * FROM users WHERE id = {user_id}"  # 위험!
cursor.execute(query)

# 안전 패턴
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# 위험 패턴 - Command Injection
os.system(f"ping {user_input}")  # 위험!

# 안전 패턴
subprocess.run(["ping", user_input], shell=False)

# 위험 패턴 - SSTI
template = Template(user_input)  # 위험!

# 안전 패턴
template = Template("Hello, {{ name }}")
template.render(name=user_input)
```

### JavaScript/Node.js

```javascript
// 위험 패턴 - SQL Injection
db.query(`SELECT * FROM users WHERE id = ${userId}`);  // 위험!

// 안전 패턴
db.query('SELECT * FROM users WHERE id = ?', [userId]);

// 위험 패턴 - XSS
element.innerHTML = userInput;  // 위험!

// 안전 패턴
element.textContent = userInput;

// 위험 패턴 - NoSQL Injection (MongoDB)
db.users.find({ username: req.body.username });  // 위험! ($ne 등 연산자 주입 가능)

// 안전 패턴
const username = String(req.body.username);  // 타입 강제
```

### SQL 검색 키워드

```
execute, query, raw, cursor, connection
f"SELECT, f"INSERT, f"UPDATE, f"DELETE
.format(, + " WHERE, + ' WHERE
```

## 검토 질문

1. 사용자 입력이 SQL 쿼리에 직접 삽입되는가?
2. 명령어 실행 시 사용자 입력이 포함되는가?
3. HTML 렌더링 시 이스케이프 처리가 되어 있는가?
4. 파일 경로에 사용자 입력이 포함되는가?

## 발견 시 보고 형식

```markdown
**[Critical]** src/db/queries.py:78

SQL 인젝션 취약점: f-string을 사용한 동적 쿼리 생성.
공격자가 `' OR '1'='1` 같은 페이로드로 쿼리를 조작할 수 있습니다.

**현재 코드**:
```python
query = f"SELECT * FROM users WHERE email = '{email}'"
```

**수정 제안**:
```python
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
```
```
