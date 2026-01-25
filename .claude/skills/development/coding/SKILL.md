# Coding Standards Skill

LLM-VA 프로젝트의 코딩 표준 및 패턴 가이드.

## Python 버전
- Python 3.10+ 기능 사용 (type hints, match statements, walrus operator)

## 타입 힌트

### 필수 사항
- 모든 함수 파라미터와 반환값에 타입 힌트 사용
- `Optional[T]`는 nullable 타입에 사용
- `Literal`은 열거형 문자열 값에 사용

### 예시
```python
from typing import Optional, Literal

def get_user(user_id: int, include_deleted: bool = False) -> Optional[User]:
    ...

def set_mode(mode: Literal["active", "passive", "idle"]) -> None:
    ...
```

## Import 구성

```python
# 1. 표준 라이브러리
import os
from typing import Optional, List

# 2. 서드파티
import yaml
from pydantic import BaseModel

# 3. 로컬
from src.config import SystemConfig
```

## Pydantic 활용

### 설정 및 데이터 검증
```python
from pydantic import BaseModel, Field, field_validator

class UserConfig(BaseModel):
    name: str
    age: int = Field(ge=0, le=150)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('name cannot be empty')
        return v.strip()
```

## 의존성 주입

### 패턴
```python
# Good: 의존성 주입
class ChatAgent:
    def __init__(self, llm_client: LLMClient, memory: MemoryModule):
        self.llm_client = llm_client
        self.memory = memory

# Bad: 내부에서 직접 생성
class ChatAgent:
    def __init__(self):
        self.llm_client = GeminiClient()  # 결합도 높음
```

## 에러 처리

### 원칙
- 도메인 에러는 커스텀 예외 사용
- 적절한 심각도로 로깅
- 비동기 예외는 graceful하게 처리

### 예시
```python
class AgentError(Exception):
    """Agent 관련 기본 예외"""
    pass

class MemoryNotFoundError(AgentError):
    """메모리 검색 실패"""
    pass

async def process():
    try:
        result = await llm_client.generate(prompt)
    except asyncio.CancelledError:
        logger.info("Generation cancelled")
        raise
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise AgentError(f"Failed to generate: {e}") from e
```

## 기존 코드 참조 규칙

**CRITICAL**: 유사한 코드 작성 시:
1. 기존 구현을 **먼저 읽고 이해**
2. 같은 **패턴, 컨벤션, 구조** 따르기
3. 기존 기능을 **제거하거나 단순화하지 않기** (명시적 요청 없으면)
4. **추측하지 말고** 코드를 읽어서 확인

## 일반 원칙

- PEP 8 준수
- 함수/클래스당 하나의 책임
- 매직 넘버 대신 상수 사용
- 주석은 Why 설명 (What 아님)
