---
name: pydantic-validation
description: Pydantic V2 검증 패턴 - LLM 출력 파싱, 스트리밍 검증, 설정 관리, 데이터 계약
---

# Pydantic V2 검증 패턴 가이드

## 핵심 원칙

1. **경계에서 검증** - 외부 입력(LLM, API, 파일)은 반드시 Pydantic으로 검증
2. **실패는 빠르게** - 잘못된 데이터는 초기에 거부
3. **타입은 문서** - 모델 정의가 곧 스키마 문서

## 패턴 1: LLM 출력 검증

```python
from pydantic import BaseModel, Field, field_validator

class EmotionAnalysis(BaseModel):
    """LLM이 반환해야 하는 감정 분석 결과"""
    emotion: str = Field(..., description="감정 레이블")
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str = Field(..., min_length=10)

    @field_validator('emotion')
    @classmethod
    def validate_emotion(cls, v: str) -> str:
        valid = {'joy', 'sadness', 'anger', 'fear', 'surprise', 'neutral'}
        if v.lower() not in valid:
            raise ValueError(f"Unknown emotion: {v}")
        return v.lower()
```

### JSON 파싱 with fallback
```python
import json
from pydantic import ValidationError

def parse_llm_response(text: str) -> EmotionAnalysis | None:
    """LLM 응답에서 JSON 추출 및 검증"""
    # JSON 블록 추출 시도
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]

    try:
        data = json.loads(text.strip())
        return EmotionAnalysis.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as e:
        logger.warning(f"Parse failed: {e}")
        return None
```

## 패턴 2: 설정 관리 (pydantic-settings)

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class LLMConfig(BaseSettings):
    """환경변수 + YAML 통합 설정"""
    model_config = SettingsConfigDict(
        env_prefix='LLM_',
        env_file='.env',
        extra='ignore'
    )

    api_key: str = Field(..., description="API 키 (필수)")
    model: str = Field(default="gpt-4", description="모델명")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, gt=0)
```

### 계층적 설정 (LLM-VA 스타일)
```python
class SystemConfig(BaseSettings):
    """src/config.py 패턴 참조"""
    llm: LLMConfig = Field(default_factory=LLMConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)

    @classmethod
    def from_yaml(cls, path: str) -> "SystemConfig":
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)
```

## 패턴 3: 스트리밍 응답 검증

```python
from pydantic import BaseModel
from typing import Generator

class StreamChunk(BaseModel):
    """스트리밍 청크 검증"""
    text: str
    is_final: bool = False

class PartialResponse(BaseModel):
    """부분 응답 (점진적 파싱)"""
    content: str = ""

    def append(self, chunk: StreamChunk) -> "PartialResponse":
        return PartialResponse(content=self.content + chunk.text)

def validate_stream(chunks: Generator[dict, None, None]) -> Generator[StreamChunk, None, None]:
    """스트리밍 청크를 검증하며 yield"""
    for raw in chunks:
        try:
            yield StreamChunk.model_validate(raw)
        except ValidationError:
            continue  # 잘못된 청크 스킵
```

## 패턴 4: 데이터 계약 (API 경계)

```python
from pydantic import BaseModel, ConfigDict

class ChatRequest(BaseModel):
    """API 요청 스키마"""
    model_config = ConfigDict(extra='forbid')  # 알 수 없는 필드 거부

    message: str = Field(..., min_length=1, max_length=10000)
    session_id: str | None = None

class ChatResponse(BaseModel):
    """API 응답 스키마"""
    response: str
    emotion: str | None = None
    latency_ms: float
```

### FastAPI 통합
```python
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    # Pydantic이 자동으로 요청 검증
    result = await process_chat(request.message)
    return ChatResponse(**result)
```

## 패턴 5: Union 타입과 Discriminator

```python
from typing import Literal, Union
from pydantic import BaseModel, Field

class TextMessage(BaseModel):
    type: Literal["text"] = "text"
    content: str

class AudioMessage(BaseModel):
    type: Literal["audio"] = "audio"
    data: bytes
    sample_rate: int = 16000

Message = Union[TextMessage, AudioMessage]

class Conversation(BaseModel):
    """discriminator로 타입 자동 판별"""
    messages: list[Message] = Field(..., discriminator='type')
```

## Anti-patterns (하지 말 것)

### 1. 검증 없이 dict 사용
```python
# BAD
def process(data: dict):
    name = data['name']  # KeyError 가능

# GOOD
class InputData(BaseModel):
    name: str

def process(data: InputData):
    name = data.name  # 타입 안전
```

### 2. 과도한 Optional
```python
# BAD - 모든 게 Optional이면 검증 의미 없음
class Config(BaseModel):
    api_key: str | None = None
    model: str | None = None

# GOOD - 필수 vs 선택 명확히
class Config(BaseModel):
    api_key: str  # 필수
    model: str = "default"  # 선택 (기본값)
```

### 3. validator에서 외부 호출
```python
# BAD - 검증 중 I/O
@field_validator('api_key')
def check_key(cls, v):
    requests.get(f"https://api/verify/{v}")  # X

# GOOD - 검증은 순수하게
@field_validator('api_key')
def check_key(cls, v):
    if not v.startswith("sk-"):
        raise ValueError("Invalid key format")
    return v
```

## LLM-VA 프로젝트 적용

### 감정 상태 모델
```python
# src/erl/ 에서 사용
class EmotionState(BaseModel):
    """Valence-Arousal 감정 상태"""
    valence: float = Field(..., ge=-1.0, le=1.0)
    arousal: float = Field(..., ge=-1.0, le=1.0)
    label: str
```

### LLM 응답 파싱
```python
# reasoner에서 LLM 출력 검증
class RationalEmotionSample(BaseModel):
    delta_v: float = Field(..., ge=-0.5, le=0.5)
    delta_a: float = Field(..., ge=-0.5, le=0.5)
    rationale: str
```

## 체크리스트

- [ ] 외부 입력이 Pydantic 모델로 검증되는가?
- [ ] 필수/선택 필드가 명확히 구분되는가?
- [ ] LLM 응답 파싱에 fallback이 있는가?
- [ ] 설정이 환경변수/파일에서 안전하게 로드되는가?
- [ ] API 스키마가 문서화되어 있는가? (model_json_schema)
