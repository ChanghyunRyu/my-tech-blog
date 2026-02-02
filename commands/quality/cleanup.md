---
name: cleanup
description: 데드 코드 및 불필요한 요소 제거를 제안합니다.
---

# /cleanup

데드 코드와 불필요한 요소를 정리합니다.

## 사용법

```
/cleanup                   # 전체 스캔
/cleanup src/              # 특정 디렉토리
/cleanup --imports         # 미사용 임포트만
/cleanup --deps            # 미사용 의존성
```

## 동작

1. 미사용 코드 탐지
2. 제거 대상 목록 생성
3. 영향도 분석
4. 제거 제안 (사용자 확인)

## 정리 대상

| 대상 | 설명 |
|------|------|
| 미사용 임포트 | import 했지만 사용 안 함 |
| 데드 코드 | 호출되지 않는 함수/클래스 |
| 미사용 변수 | 선언 후 사용 안 함 |
| 미사용 의존성 | package.json/requirements.txt |
| 중복 코드 | 유사한 코드 블록 |
| 주석 처리된 코드 | TODO 없이 주석 처리된 코드 |

## 출력 형식

```markdown
## 정리 대상

### 미사용 임포트
- `src/utils.py:5` - `import os` (미사용)
- `src/api.py:12` - `from typing import Optional` (미사용)

### 데드 코드
- `src/legacy.py` - 전체 파일 (호출 없음)
- `src/helpers.py:45-67` - `old_function()` (호출 없음)

### 미사용 의존성
- `lodash` - package.json에 있지만 사용 안 함

### 제거 영향
- 번들 크기: 약 15KB 감소 예상
- 빌드 시간: 영향 미미
```

## 옵션

| 플래그 | 효과 |
|--------|------|
| `--imports` | 임포트만 정리 |
| `--deps` | 의존성만 정리 |
| `--dry-run` | 분석만, 수정 안 함 |
