---
name: diataxis-howto
description: Diátaxis 프레임워크 기반 How-to 가이드 작성. 특정 문제를 해결하려는 사용자를 위한 실용적 지침.
---

# How-to Guide 작성 가이드

> 참고: [Diátaxis - How-to guides](https://diataxis.fr/how-to-guides/)

## 정의

How-to Guide는 **실제 문제를 해결하기 위한 방향 제시**입니다.
- 목적: 이미 역량 있는 사용자가 **특정 목표를 달성**하도록 돕기
- 비유: 요리 레시피 — "X를 만들려면?" 또는 "Y로 무엇을 만들 수 있지?"

## Tutorial과의 차이

| Tutorial | How-to |
|----------|--------|
| 학습 중심 | 작업 중심 |
| 초보자 대상 | 이미 아는 사람 대상 |
| 설명 포함 | 설명 최소화 |
| 정해진 경로 | 유연한 적용 |

## 핵심 원칙

### DO
- **문제/목표를 명확히** 제목에 명시 ("How to X")
- **실용적 단계**만 나열 — 배경 설명 X
- **유연성 허용** — 사용자 상황에 맞게 조정 가능
- **완료 조건**을 명시 — 언제 끝인지 알 수 있게

### DON'T
- 개념 설명하지 마라 → Explanation으로
- 모든 옵션 나열하지 마라 → Reference로
- 학습 과정을 설계하지 마라 → Tutorial로

## 구조 템플릿

```markdown
# How to [목표 동사구]

## 개요
이 가이드는 [목표]를 달성하는 방법을 설명합니다.

## 사전 조건
- [필요한 것 1]
- [필요한 것 2]

## 단계

### 1. [행동]
[구체적 지시]

### 2. [행동]
[구체적 지시]

## 확인
[목표 달성 여부 확인 방법]

## 문제 해결
- [일반적인 문제 1]: [해결책]
- [일반적인 문제 2]: [해결책]

## 관련 문서
- [Reference 링크]
- [다른 How-to 링크]
```

## 품질 체크리스트

- [ ] 제목이 **"How to X"** 형식인가?
- [ ] **목표가 명확**한가?
- [ ] 각 단계가 **행동 지향적**인가?
- [ ] 불필요한 **배경 설명이 없는가**?
- [ ] **완료 조건**이 명시되어 있는가?
- [ ] 일반적인 **문제 해결책**이 포함되어 있는가?

## 예시: 좋은 How-to vs 나쁜 How-to

### 나쁜 예
```
# 새 LLM Provider 추가

LLM Provider란 무엇인가요? LLM은 Large Language Model의 약자로...
(배경 설명이 너무 많음)
```

### 좋은 예
```
# How to Add a New LLM Provider

## 단계

### 1. 클라이언트 클래스 생성
`src/llmclient/` 에 새 파일 생성:

```python
# src/llmclient/my_provider.py
from src.llmclient.base import LLMClient

class MyProviderClient(LLMClient):
    ...
```

### 2. 설정에 추가
`src/config.py`의 `LLMClientConfig.provider` Literal에 추가:
```
