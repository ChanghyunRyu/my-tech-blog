---
name: streaming-tts
description: TTS 스트리밍 최적화 - 청크 단위 생성, TTFB 최소화, 자연스러운 발화 분할
---

# TTS 스트리밍 최적화 가이드

## 핵심 원칙

1. **TTFB 최소화** - Time To First Byte, 첫 오디오가 빨리 나와야 함
2. **자연스러운 분할** - 문장/구 단위로 끊어서 자연스러운 발화
3. **버퍼링 균형** - 너무 짧으면 끊김, 너무 길면 지연

## 패턴 1: 문장 단위 스트리밍

```python
import re
from typing import AsyncGenerator

class SentenceChunker:
    """LLM 출력을 문장 단위로 분할"""

    SENTENCE_END = re.compile(r'[.!?。！？]\s*')

    def __init__(self):
        self._buffer = ""

    def add_token(self, token: str) -> str | None:
        """토큰 추가, 문장 완성 시 반환"""
        self._buffer += token

        match = self.SENTENCE_END.search(self._buffer)
        if match:
            sentence = self._buffer[:match.end()]
            self._buffer = self._buffer[match.end():]
            return sentence.strip()
        return None

    def flush(self) -> str | None:
        """남은 버퍼 반환 (스트림 종료 시)"""
        if self._buffer.strip():
            result = self._buffer.strip()
            self._buffer = ""
            return result
        return None


async def stream_llm_to_tts(
    llm_stream: AsyncGenerator[str, None],
    tts_engine: "TTSEngine"
) -> AsyncGenerator[bytes, None]:
    """LLM 스트림을 TTS 오디오 스트림으로 변환"""
    chunker = SentenceChunker()

    async for token in llm_stream:
        sentence = chunker.add_token(token)
        if sentence:
            async for audio in tts_engine.synthesize_stream(sentence):
                yield audio

    # 마지막 문장 처리
    remaining = chunker.flush()
    if remaining:
        async for audio in tts_engine.synthesize_stream(remaining):
            yield audio
```

## 패턴 2: TTFB 최적화

```python
import asyncio
from typing import AsyncGenerator

class OptimizedTTSPipeline:
    """첫 오디오 출력까지의 시간 최소화"""

    def __init__(self, tts_engine, prefetch_size: int = 2):
        self.tts = tts_engine
        self.prefetch_size = prefetch_size

    async def process(
        self,
        sentences: AsyncGenerator[str, None]
    ) -> AsyncGenerator[bytes, None]:
        """문장을 미리 TTS 처리하여 지연 감소"""
        queue: asyncio.Queue[bytes | None] = asyncio.Queue(maxsize=self.prefetch_size)

        async def producer():
            async for sentence in sentences:
                audio = await self.tts.synthesize(sentence)
                await queue.put(audio)
            await queue.put(None)  # 종료 신호

        # producer를 백그라운드에서 실행
        producer_task = asyncio.create_task(producer())

        try:
            while True:
                audio = await queue.get()
                if audio is None:
                    break
                yield audio
        finally:
            producer_task.cancel()
```

### 첫 문장 우선 처리
```python
async def prioritize_first_sentence(
    llm_stream: AsyncGenerator[str, None],
    tts_engine: "TTSEngine"
) -> AsyncGenerator[bytes, None]:
    """첫 문장은 즉시 처리, 나머지는 버퍼링"""
    chunker = SentenceChunker()
    first_sent = True

    async for token in llm_stream:
        sentence = chunker.add_token(token)
        if sentence:
            if first_sent:
                # 첫 문장: 즉시 TTS
                async for audio in tts_engine.synthesize_stream(sentence):
                    yield audio
                first_sent = False
            else:
                # 이후 문장: 버퍼링 가능
                audio = await tts_engine.synthesize(sentence)
                yield audio
```

## 패턴 3: 청크 크기 최적화

```python
from dataclasses import dataclass

@dataclass
class TTSChunkConfig:
    min_chars: int = 10       # 최소 문자 수
    max_chars: int = 200      # 최대 문자 수
    target_duration_ms: int = 2000  # 목표 오디오 길이

class AdaptiveChunker:
    """적응형 청크 크기 조절"""

    def __init__(self, config: TTSChunkConfig):
        self.config = config
        self._avg_chars_per_second = 5.0  # 초기 추정치

    def update_estimate(self, text: str, duration_ms: float):
        """실제 발화 속도로 추정치 업데이트"""
        chars_per_second = len(text) / (duration_ms / 1000)
        # 이동 평균
        self._avg_chars_per_second = (
            0.8 * self._avg_chars_per_second +
            0.2 * chars_per_second
        )

    def get_target_chars(self) -> int:
        """목표 문자 수 계산"""
        target = int(
            self._avg_chars_per_second *
            (self.config.target_duration_ms / 1000)
        )
        return max(self.config.min_chars, min(target, self.config.max_chars))
```

## 패턴 4: 자연스러운 분할점

```python
import re

class NaturalBreakChunker:
    """자연스러운 발화 지점에서 분할"""

    # 우선순위별 분할점
    BREAK_PATTERNS = [
        (re.compile(r'[.!?。！？]\s*'), 1.0),     # 문장 끝
        (re.compile(r'[,;:，；：]\s*'), 0.7),     # 구두점
        (re.compile(r'\s+'), 0.3),               # 공백
    ]

    def find_break_point(self, text: str, max_len: int) -> int:
        """최적 분할 지점 찾기"""
        if len(text) <= max_len:
            return len(text)

        best_pos = max_len
        best_score = 0.0

        for pattern, score in self.BREAK_PATTERNS:
            for match in pattern.finditer(text[:max_len]):
                pos = match.end()
                if pos > max_len * 0.5:  # 최소 50% 이상에서만
                    if score > best_score:
                        best_score = score
                        best_pos = pos

        return best_pos

    def chunk(self, text: str, max_len: int = 100) -> list[str]:
        """텍스트를 자연스럽게 분할"""
        chunks = []
        remaining = text

        while remaining:
            break_pos = self.find_break_point(remaining, max_len)
            chunks.append(remaining[:break_pos].strip())
            remaining = remaining[break_pos:].strip()

        return chunks
```

## 패턴 5: TTS 엔진 추상화

```python
from abc import ABC, abstractmethod
from typing import AsyncGenerator

class TTSEngine(ABC):
    """TTS 엔진 인터페이스"""

    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        """텍스트를 오디오로 변환"""
        pass

    @abstractmethod
    async def synthesize_stream(self, text: str) -> AsyncGenerator[bytes, None]:
        """스트리밍 합성"""
        pass


class EdgeTTSEngine(TTSEngine):
    """Microsoft Edge TTS (무료)"""

    def __init__(self, voice: str = "ko-KR-SunHiNeural"):
        self.voice = voice

    async def synthesize(self, text: str) -> bytes:
        import edge_tts
        communicate = edge_tts.Communicate(text, self.voice)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return audio_data

    async def synthesize_stream(self, text: str) -> AsyncGenerator[bytes, None]:
        import edge_tts
        communicate = edge_tts.Communicate(text, self.voice)
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]


class ElevenLabsEngine(TTSEngine):
    """ElevenLabs API (고품질)"""

    def __init__(self, api_key: str, voice_id: str):
        self.api_key = api_key
        self.voice_id = voice_id

    async def synthesize_stream(self, text: str) -> AsyncGenerator[bytes, None]:
        import httpx

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream",
                headers={"xi-api-key": self.api_key},
                json={"text": text, "model_id": "eleven_multilingual_v2"}
            ) as response:
                async for chunk in response.aiter_bytes(1024):
                    yield chunk
```

## 패턴 6: 오디오 플레이백 버퍼

```python
import asyncio

class AudioPlaybackBuffer:
    """재생 끊김 방지를 위한 버퍼"""

    def __init__(self, min_buffer_ms: int = 500):
        self.min_buffer_ms = min_buffer_ms
        self._queue: asyncio.Queue[bytes] = asyncio.Queue()
        self._buffered_ms = 0

    async def add(self, audio: bytes, duration_ms: float):
        await self._queue.put((audio, duration_ms))
        self._buffered_ms += duration_ms

    async def get_when_ready(self) -> bytes:
        """충분히 버퍼링되면 오디오 반환"""
        while self._buffered_ms < self.min_buffer_ms:
            await asyncio.sleep(0.01)

        audio, duration_ms = await self._queue.get()
        self._buffered_ms -= duration_ms
        return audio
```

## LLM-VA 프로젝트 적용

### 현재 TTS 위치
```
src/audio/tts/  # TTS 구현
```

### 통합 예시
```python
async def respond_to_user(user_text: str, websocket):
    """사용자 입력에 대한 음성 응답"""

    # LLM 스트리밍 응답 생성
    llm_stream = chat_agent.generate_stream(user_text)

    # TTS 스트리밍 파이프라인
    tts = EdgeTTSEngine(voice="ko-KR-SunHiNeural")

    async for audio_chunk in stream_llm_to_tts(llm_stream, tts):
        await websocket.send_bytes(audio_chunk)
```

## 체크리스트

- [ ] 첫 오디오 출력까지 시간(TTFB)이 적절한가? (< 500ms 목표)
- [ ] 문장/구 단위로 자연스럽게 분할되는가?
- [ ] 재생 중 끊김이 없는가?
- [ ] LLM 토큰 스트리밍과 TTS가 파이프라인으로 연결되는가?
- [ ] 다양한 TTS 엔진을 교체할 수 있는 추상화가 있는가?
