---
name: improve
description: 코드 개선 제안. 리팩토링 및 최적화 방안을 분석합니다.
---

# /improve

코드 개선 방안을 제안합니다.

## 사용법

```
/improve src/services/      # 특정 디렉토리
/improve --performance      # 성능 중점
/improve --readability      # 가독성 중점
/improve --maintainability  # 유지보수성 중점
```

## 동작

1. 코드 분석
2. 개선 영역 식별
3. 구체적인 제안
4. 우선순위 제시

## 분석 영역

### 성능 (--performance)
- 시간 복잡도 개선
- 불필요한 연산 제거
- 캐싱 기회 식별
- N+1 쿼리 탐지

### 가독성 (--readability)
- 함수/변수 명명
- 코드 구조화
- 주석 개선
- 복잡도 감소

### 유지보수성 (--maintainability)
- 모듈화 개선
- 결합도 감소
- 테스트 용이성
- 기술 부채 식별

## 출력 형식

```markdown
## 개선 제안: {대상}

### 우선순위 높음
1. **{제목}** - {이유}
   현재: ...
   제안: ...

### 우선순위 중간
...

### 우선순위 낮음
...
```

## 연관 커맨드

- `/review` - 일반 코드 리뷰
- `/cleanup` - 데드 코드 제거
