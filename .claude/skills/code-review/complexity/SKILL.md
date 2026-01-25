# Complexity Review Skill

## 목적
코드가 필요 이상으로 복잡하지 않은지, 다른 개발자가 이해하고 수정할 수 있는지 평가합니다.

## 핵심 질문

1. **즉시 이해**: 코드를 읽고 바로 이해되는가?
2. **수정 용이**: 다른 개발자가 수정할 때 버그를 만들 가능성은?
3. **필요성**: 이 복잡성이 정말 필요한가?

## Google의 정의

> "코드가 빠르게 이해되지 않거나, 개발자들이 수정할 때 버그를 만들 가능성이 높으면 너무 복잡한 것이다."

## 검토 기준

### 함수 수준
| 체크 | 기준 |
|------|------|
| [ ] | 함수 길이 적절 (일반적으로 < 50줄) |
| [ ] | 중첩 깊이 < 4 |
| [ ] | 파라미터 개수 < 5 |
| [ ] | 조건문 복잡도 낮음 |
| [ ] | 한 함수 = 한 가지 일 |

### 클래스 수준
| 체크 | 기준 |
|------|------|
| [ ] | 클래스 크기 적절 |
| [ ] | 메서드 간 응집도 높음 |
| [ ] | 상속 대신 합성 고려됨 |
| [ ] | 불필요한 추상화 없음 |

### 과도한 엔지니어링 (Over-Engineering)
| 경고 | 패턴 |
|------|------|
| ⚠️ | 사용처가 하나인 인터페이스/추상 클래스 |
| ⚠️ | "나중에 필요할 수도 있어서" 추가한 기능 |
| ⚠️ | 3줄이면 되는 것을 패턴으로 풀어쓴 것 |
| ⚠️ | 설정 가능하지만 설정할 일 없는 옵션 |

## Red Flags (경고 신호)

- 🌀 깊은 중첩 (if > if > if > if)
- 📏 100줄 이상 함수
- 🎭 이름과 동작이 다른 함수
- 🔮 마법 숫자/문자열
- 🏭 단순 작업에 팩토리 패턴
- 🎪 불필요한 제네릭/메타프로그래밍

## 복잡도 지표 참고

```python
# Cyclomatic Complexity 간이 계산
# 분기문(if, elif, for, while, and, or, except) 개수 + 1
# 일반적으로 10 이하 권장
```

## 질문 예시

```markdown
**[Major]** src/services/processor.py:78

이 함수는 150줄에 중첩 깊이가 6단계입니다.
다음과 같이 분리를 제안합니다:

1. 입력 검증 → `_validate_input()`
2. 데이터 변환 → `_transform_data()`
3. 핵심 처리 → `_process_core()`
4. 결과 포맷팅 → `_format_result()`
```

```markdown
**[Major]** src/utils/factory.py:12

`ConfigFactory`가 현재 `JsonConfig` 하나만 생성합니다.
당장 다른 형식이 필요하지 않다면 팩토리 없이 직접 생성하는 게 더 단순합니다.

"현재 필요한 문제를 지금 해결하라" - Google
```

## 단순화 패턴

### 조건문 단순화
```python
# Before: 복잡한 중첩
if user:
    if user.is_active:
        if user.has_permission:
            do_something()

# After: Early return
if not user:
    return
if not user.is_active:
    return
if not user.has_permission:
    return
do_something()
```

### 추상화 제거
```python
# Before: 불필요한 추상화
class DataProcessor(ABC):
    @abstractmethod
    def process(self): pass

class JsonDataProcessor(DataProcessor):
    def process(self): ...

# After: 직접 구현 (다른 형식 필요 없다면)
class JsonProcessor:
    def process(self): ...
```

## DO / DON'T

### DO
- "이게 더 단순하게 될 수 있나?" 항상 질문
- 구체적인 단순화 방안 제시
- 현재 요구사항에 집중

### DON'T
- 복잡하지만 명확한 코드를 억지로 단순화
- "좋은 패턴이니까" 추상화 요구
- 미래 확장성을 위한 복잡성 정당화
