---
name: audio-pipeline
description: 실시간 오디오 처리 파이프라인 - VAD, ASR, 청크 처리, 레이턴시 최적화
---

# 오디오 처리 파이프라인 가이드

## 핵심 원칙

1. **레이턴시 우선** - 실시간 대화에서 지연은 치명적
2. **스트리밍 처리** - 전체 오디오 대기 없이 청크 단위 처리
3. **graceful degradation** - 일부 청크 손실 허용, 전체 파이프라인 유지

## 아키텍처 개요

```
[마이크] → [VAD] → [청크 버퍼] → [ASR] → [텍스트]
                                           ↓
[스피커] ← [오디오 합성] ← [TTS] ← [LLM 응답]
```

## 패턴 1: VAD (Voice Activity Detection)

```python
import numpy as np
from dataclasses import dataclass

@dataclass
class VADConfig:
    threshold_db: float = -40.0  # 음성 감지 임계값
    min_speech_ms: int = 250     # 최소 음성 지속 시간
    min_silence_ms: int = 500    # 최소 무음 지속 시간

class VADProcessor:
    def __init__(self, config: VADConfig, sample_rate: int = 16000):
        self.config = config
        self.sample_rate = sample_rate
        self._speech_frames = 0
        self._silence_frames = 0

    def process_chunk(self, audio: np.ndarray) -> bool:
        """청크가 음성인지 판단"""
        rms = np.sqrt(np.mean(audio ** 2))
        db = 20 * np.log10(rms + 1e-10)

        is_speech = db > self.config.threshold_db

        if is_speech:
            self._speech_frames += len(audio)
            self._silence_frames = 0
        else:
            self._silence_frames += len(audio)

        return self._is_active_speech()

    def _is_active_speech(self) -> bool:
        min_samples = int(self.config.min_speech_ms * self.sample_rate / 1000)
        return self._speech_frames >= min_samples
```

### Silero VAD 사용 (권장)
```python
import torch

class SileroVAD:
    def __init__(self):
        self.model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad'
        )
        self.get_speech_timestamps = utils[0]

    def detect(self, audio: np.ndarray, sample_rate: int = 16000) -> list[dict]:
        """음성 구간 타임스탬프 반환"""
        tensor = torch.from_numpy(audio).float()
        return self.get_speech_timestamps(
            tensor,
            self.model,
            sampling_rate=sample_rate
        )
```

## 패턴 2: 청크 버퍼링

```python
import asyncio
from collections import deque

class AudioChunkBuffer:
    """청크를 모아서 적절한 크기로 ASR에 전달"""

    def __init__(
        self,
        target_duration_ms: int = 500,
        sample_rate: int = 16000,
        max_buffer_ms: int = 5000
    ):
        self.target_samples = int(target_duration_ms * sample_rate / 1000)
        self.max_samples = int(max_buffer_ms * sample_rate / 1000)
        self._buffer: deque[np.ndarray] = deque()
        self._total_samples = 0

    def add_chunk(self, chunk: np.ndarray) -> np.ndarray | None:
        """청크 추가, 충분하면 병합된 오디오 반환"""
        self._buffer.append(chunk)
        self._total_samples += len(chunk)

        # 버퍼 오버플로우 방지
        while self._total_samples > self.max_samples:
            removed = self._buffer.popleft()
            self._total_samples -= len(removed)

        if self._total_samples >= self.target_samples:
            return self._flush()
        return None

    def _flush(self) -> np.ndarray:
        result = np.concatenate(list(self._buffer))
        self._buffer.clear()
        self._total_samples = 0
        return result
```

## 패턴 3: ASR 스트리밍

```python
from typing import AsyncGenerator

class StreamingASR:
    """실시간 음성 인식"""

    async def transcribe_stream(
        self,
        audio_stream: AsyncGenerator[np.ndarray, None]
    ) -> AsyncGenerator[str, None]:
        """오디오 스트림을 텍스트로 변환"""
        buffer = AudioChunkBuffer()

        async for chunk in audio_stream:
            merged = buffer.add_chunk(chunk)
            if merged is not None:
                text = await self._recognize(merged)
                if text:
                    yield text

    async def _recognize(self, audio: np.ndarray) -> str | None:
        # Whisper, Google Speech 등 사용
        pass
```

### Faster-Whisper 사용
```python
from faster_whisper import WhisperModel

class WhisperASR:
    def __init__(self, model_size: str = "base"):
        self.model = WhisperModel(
            model_size,
            device="cuda",
            compute_type="float16"
        )

    async def recognize(self, audio: np.ndarray) -> str:
        segments, _ = self.model.transcribe(
            audio,
            language="ko",
            vad_filter=True
        )
        return " ".join(s.text for s in segments)
```

## 패턴 4: Barge-in 감지

```python
class BargeInDetector:
    """사용자가 AI 응답 중 끼어드는 것 감지"""

    def __init__(self, threshold_db: float = -35.0, min_duration_ms: int = 200):
        self.threshold_db = threshold_db
        self.min_samples = int(min_duration_ms * 16000 / 1000)
        self._loud_samples = 0

    def check(self, audio: np.ndarray) -> bool:
        """barge-in 발생 여부"""
        rms = np.sqrt(np.mean(audio ** 2))
        db = 20 * np.log10(rms + 1e-10)

        if db > self.threshold_db:
            self._loud_samples += len(audio)
        else:
            self._loud_samples = 0

        if self._loud_samples >= self.min_samples:
            self._loud_samples = 0
            return True
        return False
```

### Barge-in 처리 흐름
```python
async def handle_conversation_turn(
    audio_input: AsyncGenerator[np.ndarray, None],
    tts_output: AsyncGenerator[bytes, None]
):
    barge_in = BargeInDetector()
    tts_task = asyncio.create_task(play_tts(tts_output))

    async for chunk in audio_input:
        if barge_in.check(chunk):
            tts_task.cancel()  # TTS 중단
            await handle_user_input(chunk)
            break
```

## 패턴 5: 레이턴시 모니터링

```python
import time
from dataclasses import dataclass, field

@dataclass
class LatencyMetrics:
    vad_ms: float = 0.0
    asr_ms: float = 0.0
    llm_ms: float = 0.0
    tts_ms: float = 0.0
    total_ms: float = field(init=False)

    def __post_init__(self):
        self.total_ms = self.vad_ms + self.asr_ms + self.llm_ms + self.tts_ms

class LatencyTracker:
    def __init__(self):
        self._start_times: dict[str, float] = {}

    def start(self, stage: str):
        self._start_times[stage] = time.perf_counter()

    def end(self, stage: str) -> float:
        elapsed = (time.perf_counter() - self._start_times[stage]) * 1000
        return elapsed
```

## 오디오 포맷 변환

```python
import numpy as np

def pcm_to_float(pcm: bytes, dtype=np.int16) -> np.ndarray:
    """PCM 바이트를 float32 배열로 변환"""
    audio = np.frombuffer(pcm, dtype=dtype)
    return audio.astype(np.float32) / np.iinfo(dtype).max

def float_to_pcm(audio: np.ndarray, dtype=np.int16) -> bytes:
    """float32 배열을 PCM 바이트로 변환"""
    scaled = (audio * np.iinfo(dtype).max).astype(dtype)
    return scaled.tobytes()

def resample(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    """샘플레이트 변환"""
    import librosa
    return librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr)
```

## LLM-VA 프로젝트 적용

### 현재 구조
```
src/audio/
├── asr/       # 음성 인식
├── tts/       # 음성 합성
└── vad/       # 음성 감지
```

### 통합 파이프라인 예시
```python
async def audio_conversation_loop(websocket):
    vad = SileroVAD()
    asr = WhisperASR()
    tracker = LatencyTracker()

    async for raw_audio in websocket:
        audio = pcm_to_float(raw_audio)

        # VAD
        tracker.start("vad")
        if not vad.is_speech(audio):
            continue
        vad_ms = tracker.end("vad")

        # ASR
        tracker.start("asr")
        text = await asr.recognize(audio)
        asr_ms = tracker.end("asr")

        # LLM + TTS는 별도 처리
        await process_user_input(text)
```

## 체크리스트

- [ ] VAD가 음성/무음을 정확히 구분하는가?
- [ ] 청크 버퍼 크기가 ASR에 적합한가? (보통 500ms~2s)
- [ ] Barge-in 감지가 작동하는가?
- [ ] 레이턴시가 실시간 대화에 적합한가? (< 500ms 목표)
- [ ] 오디오 포맷(샘플레이트, 비트깊이)이 일관적인가?
