---
name: error-handling
description: Python 에러 처리 패턴 - 커스텀 예외, 재시도 로직, graceful degradation, 로깅 전략
---

# Python 에러 처리 패턴 가이드

## 핵심 원칙

1. **실패는 빠르게** - 잘못된 상태는 조기에 감지
2. **복구 가능하면 복구** - graceful degradation 우선
3. **로그는 충분히** - 디버깅에 필요한 컨텍스트 포함
4. **사용자에게는 친절히** - 내부 에러 노출 금지

## 패턴 1: 커스텀 예외 계층

```python
class LLMVAError(Exception):
    """프로젝트 기본 예외"""
    pass

class ConfigurationError(LLMVAError):
    """설정 오류"""
    pass

class LLMClientError(LLMVAError):
    """LLM API 호출 실패"""
    def __init__(self, message: str, provider: str, status_code: int | None = None):
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code

class AudioProcessingError(LLMVAError):
    """오디오 처리 실패"""
    pass
```

### 사용
```python
def load_config(path: str) -> Config:
    if not Path(path).exists():
        raise ConfigurationError(f"Config not found: {path}")
    # ...
```

## 패턴 2: 재시도 로직 (Retry with Backoff)

```python
import asyncio
from functools import wraps
from typing import TypeVar, Callable

T = TypeVar('T')

def retry_async(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    exceptions: tuple = (Exception,)
):
    """지수 백오프 재시도 데코레이터"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        delay = base_delay * (2 ** attempt)
                        await asyncio.sleep(delay)
            raise last_error
        return wrapper
    return decorator

# 사용
@retry_async(max_attempts=3, exceptions=(LLMClientError,))
async def call_llm(prompt: str) -> str:
    return await client.generate(prompt)
```

### tenacity 라이브러리 사용 (권장)
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
async def call_llm_with_tenacity(prompt: str) -> str:
    return await client.generate(prompt)
```

## 패턴 3: Graceful Degradation

```python
async def get_emotion_with_fallback(text: str) -> EmotionState:
    """감정 분석 실패 시 기본값 반환"""
    try:
        return await mecot_engine.analyze(text)
    except LLMClientError as e:
        logger.warning(f"MECoT failed, using fallback: {e}")
        return EmotionState(valence=0.0, arousal=0.0, label="neutral")
    except Exception as e:
        logger.error(f"Unexpected error in emotion analysis: {e}")
        return EmotionState(valence=0.0, arousal=0.0, label="neutral")
```

### Optional 결과 패턴
```python
from typing import Optional

async def try_get_memory(query: str) -> Optional[Memory]:
    """메모리 검색 실패 시 None 반환"""
    try:
        return await memory_store.search(query)
    except Exception as e:
        logger.warning(f"Memory search failed: {e}")
        return None

# 호출 측
memory = await try_get_memory(query)
if memory:
    context = memory.content
else:
    context = ""  # 메모리 없이 진행
```

## 패턴 4: 컨텍스트 매니저 에러 처리

```python
from contextlib import asynccontextmanager
from typing import AsyncGenerator

@asynccontextmanager
async def managed_llm_session() -> AsyncGenerator[LLMClient, None]:
    """리소스 정리 보장"""
    client = await LLMClient.connect()
    try:
        yield client
    except LLMClientError:
        logger.error("LLM session error, will reconnect")
        raise
    finally:
        await client.close()

# 사용
async with managed_llm_session() as client:
    response = await client.generate(prompt)
```

## 패턴 5: 구조화된 로깅

```python
import logging
import structlog

# structlog 설정 (권장)
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

async def process_message(message: str, session_id: str):
    log = logger.bind(session_id=session_id)

    try:
        log.info("processing_message", length=len(message))
        result = await handle(message)
        log.info("message_processed", latency_ms=result.latency)
        return result
    except LLMClientError as e:
        log.error("llm_call_failed",
                  provider=e.provider,
                  status_code=e.status_code)
        raise
```

### 로깅 레벨 가이드
| 레벨 | 용도 | 예시 |
|------|------|------|
| DEBUG | 개발 디버깅 | 변수 값, 함수 진입/종료 |
| INFO | 정상 동작 기록 | 요청 처리, 작업 완료 |
| WARNING | 복구 가능한 문제 | fallback 사용, 재시도 |
| ERROR | 복구 불가능한 오류 | API 실패, 파일 없음 |
| CRITICAL | 시스템 중단 | 설정 오류, 필수 의존성 없음 |

## 패턴 6: 에러 집계 및 전파

```python
async def process_batch(items: list[str]) -> BatchResult:
    """여러 항목 처리, 일부 실패 허용"""
    results = []
    errors = []

    for item in items:
        try:
            result = await process_item(item)
            results.append(result)
        except Exception as e:
            errors.append(ItemError(item=item, error=str(e)))

    if errors and not results:
        # 전체 실패
        raise BatchProcessingError(f"All {len(errors)} items failed", errors)

    return BatchResult(
        successful=results,
        failed=errors,
        success_rate=len(results) / len(items)
    )
```

## Anti-patterns (하지 말 것)

### 1. 빈 except
```python
# BAD - 모든 에러 무시
try:
    process()
except:
    pass

# GOOD - 특정 예외만 처리
try:
    process()
except ValueError as e:
    logger.warning(f"Invalid value: {e}")
    use_default()
```

### 2. 예외를 문자열로 판단
```python
# BAD
try:
    call_api()
except Exception as e:
    if "rate limit" in str(e):  # 취약
        wait()

# GOOD - 명시적 예외 타입
try:
    call_api()
except RateLimitError:
    wait()
```

### 3. 로그 없이 재발생
```python
# BAD - 컨텍스트 손실
try:
    process()
except Exception:
    raise

# GOOD - 로깅 후 재발생
try:
    process()
except Exception as e:
    logger.error(f"Process failed: {e}", exc_info=True)
    raise
```

## LLM-VA 프로젝트 적용

### LLM 클라이언트 에러 처리
```python
# src/llmclient/ 패턴
async def generate(self, prompt: str) -> str:
    try:
        response = await self._call_api(prompt)
        return response.text
    except httpx.TimeoutException:
        raise LLMClientError("Request timeout", provider=self.provider)
    except httpx.HTTPStatusError as e:
        raise LLMClientError(
            f"API error: {e.response.status_code}",
            provider=self.provider,
            status_code=e.response.status_code
        )
```

### 오디오 파이프라인 복구
```python
# src/audio/ 패턴
async def process_audio_stream(stream):
    async for chunk in stream:
        try:
            await process_chunk(chunk)
        except AudioProcessingError as e:
            logger.warning(f"Chunk skipped: {e}")
            continue  # 청크 스킵하고 계속
```

## 체크리스트

- [ ] 외부 호출(API, 파일, 네트워크)에 예외 처리가 있는가?
- [ ] 커스텀 예외가 적절한 컨텍스트를 포함하는가?
- [ ] 재시도 로직이 필요한 곳에 적용되었는가?
- [ ] 로그에 디버깅에 필요한 정보가 포함되는가?
- [ ] 사용자에게 내부 에러 메시지가 노출되지 않는가?
- [ ] 리소스 정리가 finally/컨텍스트매니저로 보장되는가?
