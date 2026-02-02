---
name: plan
description: 구현 계획 작성. 작업을 단계별로 분해합니다.
skill: practices/planning
---

# /plan

구현 계획을 작성합니다.

## 사용법

```
/plan API 엔드포인트 추가
/plan --detailed 결제 연동
/plan --dependencies 마이그레이션
```

## 동작

1. 목표 명확화
2. 작업 분해 (WBS)
3. 의존성 파악
4. 순서 결정
5. 체크리스트 생성

## 출력 형식

```markdown
## 구현 계획: {목표}

### 작업 분해
1. [ ] 작업 1
   - [ ] 하위 작업 1.1
   - [ ] 하위 작업 1.2
2. [ ] 작업 2
   ...

### 의존성
- 작업 2 → 작업 1 완료 필요
- 작업 3 → 외부 API 문서 필요

### 우선순위
1. 작업 1 (블로커)
2. 작업 3 (병렬 가능)
3. 작업 2
```

## 옵션

| 플래그 | 효과 |
|--------|------|
| `--detailed` | 더 세부적인 분해 |
| `--dependencies` | 의존성 그래프 강조 |
| `--parallel` | 병렬 가능 작업 식별 |

## 스킬 참조

- `.claude/skills/practices/planning/`
