from __future__ import annotations

import math
import math
from dataclasses import dataclass
from typing import Iterable, Optional

import numpy as np
from TTS.api import TTS


@dataclass
class MelGeneratorConfig:
    n_mels: int = 80
    frames_per_phoneme: int = 12
    noise_std: float = 0.01
    seed: int = 13
    sample_rate: int = 22050


@dataclass
class MelOutput:
    mel: Optional[np.ndarray]
    audio: Optional[np.ndarray]
    sample_rate: int


class MelSpectrogramGenerator:
    """간단한 mock mel generator (테스트/비교용)."""

    def __init__(self, config: MelGeneratorConfig | None = None) -> None:
        self.config = config or MelGeneratorConfig()
        self._rng = np.random.default_rng(self.config.seed)

    def generate(self, phonemes: Iterable[str], text: str | None = None) -> MelOutput:
        frames = []
        for idx, phoneme in enumerate(phonemes):
            base_vector = self._phoneme_to_vector(phoneme, idx)
            for _ in range(self.config.frames_per_phoneme):
                noise = self._rng.normal(0, self.config.noise_std, self.config.n_mels)
                frames.append(base_vector + noise)
        if not frames:
            mel = np.zeros((1, self.config.n_mels), dtype=np.float32)
        else:
            mel = np.stack(frames).astype(np.float32)
            mel = np.clip(mel, 0.0, 1.0)
        return MelOutput(mel=mel, audio=None, sample_rate=self.config.sample_rate)

    def _phoneme_to_vector(self, phoneme: str, position: int) -> np.ndarray:
        idx = (sum(ord(ch) for ch in phoneme) + position * 17) % self.config.n_mels
        ramp = np.linspace(0.1, 0.9, self.config.n_mels)
        rotated = np.roll(ramp, idx)
        modulator = 0.5 * (1 + np.sin(np.linspace(0, math.pi, self.config.n_mels)))
        vector = rotated * modulator
        return vector


@dataclass
class VITSGeneratorConfig:
    model_name: str = "tts_models/ko/kss/vits"
    speaker: str | None = None
    use_cuda: bool | None = None
    speed: float = 1.0


class VITSMelSpectrogramGenerator:
    """Coqui TTS VITS 모델을 이용해 직접 오디오를 생성한다."""

    def __init__(self, config: VITSGeneratorConfig | None = None) -> None:
        self.config = config or VITSGeneratorConfig()
        self._tts = TTS(
            model_name=self.config.model_name,
            progress_bar=False,
            gpu=self.config.use_cuda,
        )
        self.sample_rate = int(self._tts.synthesizer.output_sample_rate)

    def generate(self, phonemes: Iterable[str], text: str | None = None) -> MelOutput:
        sentence = text or "".join(phonemes)
        if not sentence:
            return MelOutput(
                mel=None,
                audio=np.zeros(1, dtype=np.float32),
                sample_rate=self.sample_rate,
            )
        audio = self._tts.tts(
            sentence,
            speaker=self.config.speaker,
            speed=self.config.speed,
        )
        audio_arr = np.asarray(audio, dtype=np.float32)
        return MelOutput(mel=None, audio=audio_arr, sample_rate=self.sample_rate)

