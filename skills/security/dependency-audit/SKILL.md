# Dependency Audit Skill

## 목적
프로젝트 의존성에서 알려진 취약점을 탐지합니다.

## OWASP A06:2025 - Vulnerable and Outdated Components

취약하거나, 지원이 중단되었거나, 오래된 구성 요소를 사용할 때 발생합니다.

## 체크리스트

| 체크 | 항목 | 심각도 |
|------|------|--------|
| [ ] | 알려진 취약점이 있는 패키지 없음 | Critical~Low |
| [ ] | 지원 중단된 패키지 없음 | Medium |
| [ ] | 의존성 버전 고정 (lockfile 존재) | Medium |
| [ ] | 정기적 의존성 업데이트 프로세스 존재 | Low |
| [ ] | 불필요한 의존성 없음 | Low |

## 점검 방법

### Python (pip)

```bash
# 취약점 스캔
pip-audit

# 또는
safety check

# 의존성 트리 확인
pip show <package>
pipdeptree
```

**의존성 파일**: `requirements.txt`, `pyproject.toml`, `Pipfile.lock`

### Node.js (npm/yarn)

```bash
# 취약점 스캔
npm audit

# 또는
yarn audit

# 자동 수정 (주의해서 사용)
npm audit fix
```

**의존성 파일**: `package.json`, `package-lock.json`, `yarn.lock`

### Go

```bash
# 취약점 스캔
govulncheck ./...
```

**의존성 파일**: `go.mod`, `go.sum`

## Red Flags (경고 신호)

- `package-lock.json` 또는 `yarn.lock` 부재
- `requirements.txt`에 버전 지정 없음 (`requests` vs `requests==2.28.0`)
- 2년 이상 업데이트 없는 패키지
- 알려진 CVE가 있는 패키지
- 비공식 또는 포크된 패키지 사용

## 검토 패턴

### Python requirements.txt

```txt
# 위험 패턴 - 버전 미지정
requests
flask
django

# 안전 패턴 - 버전 고정
requests==2.31.0
flask==3.0.0
django==5.0.0

# 또는 최소 버전 지정
requests>=2.31.0,<3.0.0
```

### Node.js package.json

```json
{
  "dependencies": {
    // 위험 패턴 - 너무 넓은 범위
    "lodash": "*",
    "express": "latest",

    // 안전 패턴
    "lodash": "^4.17.21",
    "express": "~4.18.2"
  }
}
```

## 주요 취약점 데이터베이스

- [NVD (National Vulnerability Database)](https://nvd.nist.gov/)
- [GitHub Advisory Database](https://github.com/advisories)
- [Snyk Vulnerability DB](https://snyk.io/vuln/)
- [PyPI Advisory Database](https://pypi.org/project/pip-audit/)

## 검토 질문

1. lockfile이 존재하고 커밋되어 있는가?
2. 마지막 의존성 업데이트가 언제인가?
3. 사용하지 않는 의존성이 있는가?
4. 내부/비공식 패키지를 사용하는가?

## 발견 시 보고 형식

```markdown
**[High]** package.json

취약한 의존성 발견: `lodash@4.17.15`에 프로토타입 오염 취약점 (CVE-2020-8203).

**영향**:
공격자가 객체 프로토타입을 오염시켜 서비스 거부 또는 임의 코드 실행 가능.

**수정 제안**:
```bash
npm install lodash@4.17.21
```

또는 `package.json` 수정:
```json
"lodash": "^4.17.21"
```
```

## 자동화 권장

CI/CD 파이프라인에 의존성 스캔 추가:

```yaml
# GitHub Actions 예시
- name: Security Audit
  run: |
    npm audit --audit-level=high
    # 또는
    pip-audit --strict
```
