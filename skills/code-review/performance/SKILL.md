# Performance Review Skill

## 목적
코드의 성능 문제를 식별하고 개선안을 제시합니다.

## 핵심 질문

1. **시간**: 이 코드의 시간 복잡도가 적절한가?
2. **공간**: 메모리 사용이 효율적인가?
3. **I/O**: 불필요한 I/O 작업이 있는가?
4. **확장**: 데이터가 커지면 어떻게 될까?

## 체크리스트

### 시간 복잡도

| 체크 | 기준 | 영향 |
|------|------|------|
| [ ] | 불필요한 중첩 루프 없음 (O(n^2) 이상 주의) | High |
| [ ] | 적절한 자료구조 사용 (List vs Set/Map) | High |
| [ ] | 조기 종료 조건 활용 | Medium |
| [ ] | 불필요한 정렬/검색 반복 없음 | Medium |

### 메모리

| 체크 | 기준 | 영향 |
|------|------|------|
| [ ] | 대용량 데이터 스트리밍/페이지네이션 | High |
| [ ] | 불필요한 복사 없음 | Medium |
| [ ] | 메모리 누수 패턴 없음 | High |
| [ ] | 제너레이터/이터레이터 활용 | Medium |

### I/O

| 체크 | 기준 | 영향 |
|------|------|------|
| [ ] | N+1 쿼리 문제 없음 | Critical |
| [ ] | 적절한 캐싱 적용 | High |
| [ ] | 비동기 I/O 활용 (해당 시) | Medium |
| [ ] | 배치 처리 활용 | Medium |

## Red Flags (경고 신호)

- 루프 내 DB 쿼리/API 호출
- 전체 데이터 메모리 로드
- 동기 블로킹 I/O (async 컨텍스트)
- 문자열 연결 in 루프 (Python)
- 리스트에서 in 연산 (Set 대신)
- 매번 재계산되는 값

## 언어별 패턴

### Python

```python
# 위험 패턴 - N+1 쿼리
for user in users:
    orders = db.query(f"SELECT * FROM orders WHERE user_id = {user.id}")

# 개선 - JOIN 또는 IN 쿼리
user_ids = [u.id for u in users]
orders = db.query("SELECT * FROM orders WHERE user_id IN (?)", user_ids)

# 위험 패턴 - 리스트에서 검색
if item in large_list:  # O(n)

# 개선 - Set 사용
large_set = set(large_list)
if item in large_set:  # O(1)

# 위험 패턴 - 전체 로드
data = list(db.query("SELECT * FROM huge_table"))  # 메모리 폭발

# 개선 - 페이지네이션/스트리밍
for batch in db.query(...).yield_per(1000):
    process(batch)

# 위험 패턴 - 문자열 연결
result = ""
for item in items:
    result += str(item)  # O(n^2)

# 개선
result = "".join(str(item) for item in items)  # O(n)
```

### JavaScript

```javascript
// 위험 패턴 - 루프 내 await
for (const id of ids) {
    const data = await fetch(`/api/${id}`);  // 순차 실행
}

// 개선 - 병렬 실행
const results = await Promise.all(
    ids.map(id => fetch(`/api/${id}`))
);

// 위험 패턴 - 반복 DOM 접근
for (let i = 0; i < 1000; i++) {
    document.getElementById('list').innerHTML += `<li>${i}</li>`;
}

// 개선 - 일괄 업데이트
const items = Array.from({length: 1000}, (_, i) => `<li>${i}</li>`);
document.getElementById('list').innerHTML = items.join('');
```

## 검토 질문

1. 입력 크기가 10배가 되면 이 코드는 얼마나 느려지는가?
2. 루프 안에서 I/O 작업이 일어나는가?
3. 같은 계산이 반복되는가?
4. 더 효율적인 자료구조가 있는가?

## 발견 시 보고 형식

```markdown
**[Performance - High]** src/services/report.py:78

N+1 쿼리 문제: 각 사용자마다 별도 쿼리 실행 (100명 = 101 쿼리).

**현재 코드**:
```python
for user in users:
    orders = Order.query.filter_by(user_id=user.id).all()
```

**수정 제안**:
```python
from sqlalchemy.orm import joinedload
users = User.query.options(joinedload(User.orders)).all()
```

**예상 개선**: 쿼리 수 101 → 1 (약 100배 개선)
```

## DO / DON'T

### DO
- 실제 데이터 크기 고려
- 병목 지점 명확히 지적
- 구체적인 개선안 제시
- 예상 개선 효과 언급

### DON'T
- 마이크로 최적화에 집착
- 측정 없이 성능 문제 단정
- 가독성 희생하는 최적화 권장
- 모든 코드에 캐싱 요구
