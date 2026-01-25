# Naming Review Skill

## 목적
변수, 함수, 클래스, 파일 이름이 명확하고 의도를 잘 전달하는지 평가합니다.

## 핵심 원칙

> "좋은 이름은 코드를 자기 문서화(self-documenting)하게 만든다."

## 검토 기준

### 명확성
| 체크 | 기준 |
|------|------|
| [ ] | 이름만으로 목적을 알 수 있음 |
| [ ] | 약어 사용이 적절함 (널리 알려진 것만) |
| [ ] | 오해의 소지 없음 |
| [ ] | 발음 가능 |

### 일관성
| 체크 | 기준 |
|------|------|
| [ ] | 프로젝트 네이밍 컨벤션 준수 |
| [ ] | 같은 개념에 같은 이름 사용 |
| [ ] | 언어별 관례 준수 (snake_case, camelCase 등) |

### 적절한 길이
| 범위 | 권장 길이 | 예시 |
|------|-----------|------|
| 루프 변수 | 1-3자 | `i`, `idx`, `item` |
| 지역 변수 | 짧음 | `user`, `count` |
| 함수/메서드 | 동사 + 명사 | `get_user()`, `validate_input()` |
| 클래스 | 명사 | `UserService`, `OrderProcessor` |
| 상수 | 명확하게 | `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT` |

## Red Flags (경고 신호)

| 패턴 | 문제 | 개선 |
|------|------|------|
| `data`, `info`, `temp` | 의미 없음 | 구체적인 이름 |
| `doStuff()`, `process()` | 너무 모호 | 무엇을 하는지 명시 |
| `userDataInfoList` | 과하게 김 | `users` |
| `a`, `x`, `foo` | 의미 전무 | 의미 있는 이름 |
| `Manager`, `Handler`, `Processor` 남용 | God Object 징후 | 구체적 역할 명시 |

## 네이밍 패턴

### 함수/메서드
```python
# 조회: get_, find_, fetch_
get_user_by_id()
find_active_orders()

# 계산: calculate_, compute_
calculate_total_price()

# 검증: is_, has_, can_, validate_
is_valid_email()
has_permission()
validate_input()

# 변환: to_, from_, convert_, parse_
to_json()
from_dict()
parse_response()

# 생성: create_, build_, generate_
create_order()
build_query()
```

### 불린 변수
```python
# Good: 질문 형태
is_active = True
has_children = False
can_edit = True
should_update = False

# Bad: 모호함
flag = True
status = False
```

### 컬렉션
```python
# Good: 복수형
users = []
order_items = {}

# Bad: 단수형
user = []  # 혼란스러움
```

## 질문 예시

```markdown
**[Minor]** src/utils/helper.py:34

`process_data(d)` - `d`가 무엇인지, 무슨 처리를 하는지 알 수 없습니다.

제안: `validate_user_input(user_input)` 또는 실제 동작에 맞는 이름
```

```markdown
Nit: src/services/order.py:89

`temp_list`는 임시 저장 목적이 명확하지만,
`pending_items` 같이 내용을 나타내는 이름이 더 좋습니다.
```

## 언어별 컨벤션

### Python (PEP 8)
```python
# 변수, 함수: snake_case
user_name = "John"
def get_user(): pass

# 클래스: PascalCase
class UserService: pass

# 상수: UPPER_SNAKE_CASE
MAX_CONNECTIONS = 100

# Private: _prefix
_internal_cache = {}
```

### JavaScript/TypeScript
```javascript
// 변수, 함수: camelCase
const userName = "John";
function getUser() {}

// 클래스: PascalCase
class UserService {}

// 상수: UPPER_SNAKE_CASE 또는 camelCase
const MAX_CONNECTIONS = 100;
```

## DO / DON'T

### DO
- 코드의 의도가 드러나는 이름 권장
- 프로젝트 기존 컨벤션 우선
- 대안 제시

### DON'T
- 사소한 선호도 차이로 변경 요구
- 이미 널리 사용되는 약어 거부 (API, URL, ID 등)
- 모든 약어를 풀어쓰라고 요구
