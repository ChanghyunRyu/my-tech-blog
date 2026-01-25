# Style Review Skill

## 목적
코드가 프로젝트/언어의 스타일 가이드를 따르는지 평가합니다.

## 핵심 원칙

> "스타일 가이드는 절대적 권위. 가이드에 없는 사항은 개인 선호의 영역."

## Google의 규칙

1. **공식 스타일 가이드** > 로컬 일관성 > 개인 선호
2. 스타일 이슈는 `Nit:` 접두사로 표시
3. 스타일만으로 승인을 막지 않음 (Critical/Major 아님)

## 검토 기준

### Python (PEP 8 기반)
| 항목 | 규칙 |
|------|------|
| 들여쓰기 | 스페이스 4칸 |
| 줄 길이 | 79자 (또는 프로젝트 설정) |
| import 순서 | 표준 → 서드파티 → 로컬 |
| 공백 | 연산자 주변, 콤마 뒤 |
| 빈 줄 | 함수/클래스 사이 2줄 |

### JavaScript/TypeScript
| 항목 | 규칙 |
|------|------|
| 세미콜론 | 프로젝트 설정 따름 |
| 따옴표 | 싱글/더블 프로젝트 설정 |
| 들여쓰기 | 2칸 또는 4칸 |
| 중괄호 | 같은 줄 or 새 줄 (프로젝트 설정) |

## 자동화 도구 우선

### 포맷터가 있는 프로젝트
```
스타일 이슈 발견 → 포맷터 실행 권장 (직접 수정 요청 X)
```

| 언어 | 포맷터 |
|------|--------|
| Python | Black, autopep8, YAPF |
| JavaScript/TypeScript | Prettier, ESLint --fix |
| Go | gofmt |
| Rust | rustfmt |

### 예시
```markdown
Nit: 전반적인 포맷팅 이슈가 있습니다.
`black .` 또는 `prettier --write .` 실행을 권장합니다.
```

## Red Flags (경고 신호)

- 🔀 일관성 없는 스타일 (같은 파일 내)
- 📏 극단적으로 긴 줄 (200자+)
- 🚫 린터 규칙 무시 주석 (`# noqa`, `// eslint-disable`)
- 🔧 설정 파일과 맞지 않는 스타일

## Nit 사용 가이드

### Nit으로 표시
```markdown
Nit: `user_list` → `users` (컬렉션은 복수형 권장)

Nit: 빈 줄이 3줄인데, 2줄로 줄이면 좋겠습니다.

Nit: import 순서가 알파벳 순이 아닙니다 (isort 권장)
```

### Nit 아닌 것 (더 높은 심각도)
```markdown
**[Minor]** 탭과 스페이스가 혼용되어 있습니다.
에디터 설정에 따라 들여쓰기가 깨질 수 있습니다.
```

## 일관성 규칙

### 1. 기존 코드 우선
```python
# 프로젝트가 single quote를 사용하면
name = 'John'  # ✅ 프로젝트 스타일
name = "John"  # ❌ 개인 선호

# 프로젝트가 double quote를 사용하면 반대
```

### 2. 같은 파일 내 일관성
```python
# 같은 파일에서 혼용 금지
config = {'key': 'value'}  # dict
config = {"key": "value"}  # 같은 파일에서 혼용 ❌
```

## 질문 예시

```markdown
Nit: src/utils/parser.py:45

```python
def parse( input ):  # 공백 불일치
```

PEP 8에 따르면 괄호 안쪽 공백은 제거합니다:
```python
def parse(input):
```
```

```markdown
Nit: 이 파일은 Black 포맷이 적용되지 않은 것 같습니다.
프로젝트에서 Black을 사용한다면 `black src/utils/parser.py` 실행을 권장합니다.
```

## DO / DON'T

### DO
- 자동화 도구 사용 권장
- 스타일 이슈는 `Nit:` 표시
- 프로젝트 기존 스타일 존중

### DON'T
- 스타일만으로 PR 거부
- 개인 선호 스타일 강요
- 포맷터가 있는데 수동 수정 요구
- 스타일 가이드에 없는 규칙 강요
