---
name: diataxis-reference
description: Diátaxis 프레임워크 기반 Reference 문서 작성. 정확하고 완전한 기술 정보 제공.
---

# Reference 문서 작성 가이드

> 참고: [Diátaxis - Reference](https://diataxis.fr/reference/)

## 정의

Reference는 **기술적 사실의 정확한 기술**입니다.
- 목적: 작업 중 **정확한 정보를 빠르게 조회**
- 비유: 지도, 사전 — 사실만, 해석 없이

## 핵심 특성

- **정확성**: 코드와 100% 일치
- **완전성**: 모든 공개 인터페이스 포함
- **구조화**: 일관된 형식으로 빠른 검색
- **객관성**: 의견이나 설명 없이 사실만

## 핵심 원칙

### DO
- **코드 구조를 따르라** — 코드가 기준
- **일관된 형식** 유지 — 모든 항목이 같은 패턴
- **모든 옵션/파라미터** 문서화
- **기본값, 타입, 제약조건** 명시
- **빠른 탐색**을 위한 인덱스/목차 제공

### DON'T
- 사용법 설명하지 마라 → How-to로
- 개념 설명하지 마라 → Explanation으로
- 학습 순서 고려하지 마라 → 알파벳/논리적 순서

## 구조 템플릿

### API/모듈 Reference
```markdown
# [모듈명] Reference

## 개요
| 항목 | 값 |
|------|-----|
| 경로 | `src/module/file.py` |
| 의존성 | `dependency1`, `dependency2` |

## 클래스

### `ClassName`

#### 설명
[한 줄 설명]

#### 생성자
```python
ClassName(param1: Type1, param2: Type2 = default)
```

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| param1 | Type1 | 필수 | 설명 |
| param2 | Type2 | default | 설명 |

#### 메서드

##### `method_name()`
```python
def method_name(arg: Type) -> ReturnType
```
[한 줄 설명]

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| arg | Type | 설명 |

| 반환값 | 설명 |
|--------|------|
| ReturnType | 설명 |

| 예외 | 조건 |
|------|------|
| ValueError | 조건 설명 |
```

### 설정 Reference
```markdown
# Configuration Reference

## `section.option`

| 항목 | 값 |
|------|-----|
| 타입 | `string` |
| 기본값 | `"default"` |
| 필수 | 아니오 |
| 환경변수 | `SECTION_OPTION` |

설명: [한 줄 설명]

유효한 값:
- `"value1"`: 설명
- `"value2"`: 설명
```

## 품질 체크리스트

- [ ] **코드와 일치**하는가? (최신 상태)
- [ ] **모든 공개 인터페이스**가 문서화되었는가?
- [ ] **일관된 형식**을 따르는가?
- [ ] **타입, 기본값, 제약조건**이 명시되어 있는가?
- [ ] **빠른 검색**이 가능한 구조인가?

## 유지보수

Reference는 **코드와 동기화**되어야 합니다:
- 코드 변경 시 반드시 Reference 업데이트
- 자동화된 검증 권장 (docstring 추출 등)
