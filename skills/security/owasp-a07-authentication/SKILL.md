# Authentication Review Skill

## 목적
인증 및 세션 관리 관련 취약점을 탐지합니다.

## OWASP A07:2025 - Identification and Authentication Failures

사용자 신원 확인, 인증, 세션 관리가 공격에 취약할 때 발생합니다.

## 체크리스트

| 체크 | 항목 | 심각도 |
|------|------|--------|
| [ ] | 강력한 비밀번호 정책 적용 (최소 길이, 복잡도) | High |
| [ ] | 비밀번호가 안전하게 해싱됨 (bcrypt, argon2) | Critical |
| [ ] | 무차별 대입 공격 방지 (Rate Limiting, CAPTCHA) | High |
| [ ] | 세션 토큰이 안전하게 생성됨 (충분한 엔트로피) | High |
| [ ] | 세션 만료 정책 존재 | Medium |
| [ ] | 로그아웃 시 세션 무효화 | Medium |
| [ ] | 민감 정보 로깅 금지 | High |
| [ ] | 비밀번호 평문 저장 금지 | Critical |

## Red Flags (경고 신호)

- MD5, SHA1으로 비밀번호 해싱
- 비밀번호 평문 저장 또는 로깅
- 하드코딩된 비밀번호/API 키
- 짧은 세션 토큰 (< 128비트)
- 무제한 로그인 시도 허용
- "비밀번호가 틀립니다" vs "사용자가 없습니다" 구분 (사용자 열거)

## 언어별 검토 패턴

### Python

```python
# 위험 패턴 - 약한 해싱
import hashlib
hashed = hashlib.md5(password.encode()).hexdigest()  # 위험!
hashed = hashlib.sha256(password.encode()).hexdigest()  # salt 없이 위험!

# 안전 패턴
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed = pwd_context.hash(password)

# 위험 패턴 - 하드코딩된 비밀
API_KEY = "sk-1234567890abcdef"  # 위험!

# 안전 패턴
API_KEY = os.environ.get("API_KEY")

# 위험 패턴 - 민감 정보 로깅
logger.info(f"User login: {username}, password: {password}")  # 위험!

# 안전 패턴
logger.info(f"User login attempt: {username}")
```

### JavaScript/Node.js

```javascript
// 위험 패턴 - 약한 해싱
const crypto = require('crypto');
const hash = crypto.createHash('md5').update(password).digest('hex');  // 위험!

// 안전 패턴
const bcrypt = require('bcrypt');
const hash = await bcrypt.hash(password, 12);

// 위험 패턴 - JWT 검증 부재
const decoded = jwt.decode(token);  // 검증 없음!

// 안전 패턴
const decoded = jwt.verify(token, process.env.JWT_SECRET);

// 위험 패턴 - 사용자 열거
if (!user) return res.json({ error: "User not found" });
if (!validPassword) return res.json({ error: "Wrong password" });

// 안전 패턴
if (!user || !validPassword) {
    return res.json({ error: "Invalid credentials" });
}
```

## 검색 키워드

```
password, secret, token, api_key, credential
md5, sha1, sha256 (salt 없이)
bcrypt, argon2, scrypt, pbkdf2
login, authenticate, session, jwt
```

## 검토 질문

1. 비밀번호는 어떤 알고리즘으로 해싱되는가?
2. 로그인 실패 시 시도 횟수 제한이 있는가?
3. 세션 토큰은 어떻게 생성되고 관리되는가?
4. 민감 정보가 로그에 기록되는가?
5. 비밀 값이 코드에 하드코딩되어 있는가?

## 발견 시 보고 형식

```markdown
**[Critical]** src/auth/hash.py:23

약한 비밀번호 해싱: MD5 사용. 레인보우 테이블 공격에 취약합니다.

**현재 코드**:
```python
hashed = hashlib.md5(password.encode()).hexdigest()
```

**수정 제안**:
```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed = pwd_context.hash(password)
```
```
