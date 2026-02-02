---
name: research
description: 심층 조사 수행. research-orchestrator를 호출합니다.
agent: research-orchestrator
---

# /research

심층 조사를 수행합니다.

## 사용법

```
/research "React 19 새 기능"
/research --depth deep "GraphQL vs REST"
/research --exhaustive "마이크로서비스 아키텍처"
```

## 동작

1. 질문 분석
2. 쿼리 계획 수립
3. 멀티홉 검색 (최대 10회)
4. 결과 종합
5. 보고서 작성

## 연구 깊이

| 레벨 | 검색 횟수 | 용도 |
|------|----------|------|
| `quick` | 1-2 | 단순 사실 확인 |
| `standard` | 3-4 | 일반 연구 (기본) |
| `deep` | 5-7 | 기술 분석 |
| `exhaustive` | 8-10 | 종합 보고서 |

## 출력

```
docs/research/YYYY-MM-DD-{topic}.md
```

### 보고서 구조

```markdown
# 연구 보고서: {주제}

## 요약
{핵심 발견 3-5개}

## 연구 과정
| 홉 | 쿼리 | 발견 | 신뢰도 |
|-----|------|------|--------|

## 상세 분석
{섹션별 상세}

## 출처
{신뢰도별 분류}

## 불확실한 영역
{추가 조사 필요}
```

## 옵션

| 플래그 | 효과 |
|--------|------|
| `--depth` | 연구 깊이 지정 |
| `--focus` | 특정 측면 집중 |
| `--compare` | 비교 분석 |
