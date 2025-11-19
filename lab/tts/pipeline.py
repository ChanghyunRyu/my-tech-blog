from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .mel_generator import (
    MelOutput,
    MelSpectrogramGenerator,
    VITSMelSpectrogramGenerator,
)
from .normalizer import TextNormalizer
from .phonemizer import KoreanG2PPhonemizer
from .vocoder import SimpleVocoder


@dataclass
class TTSSample:
    text: str
    normalized_text: str
    phonemes: list[str]
    mel: np.ndarray | None
    audio: np.ndarray
    sample_rate: int


class TTSPipeline:
    """텍스트 → phoneme → mel → 오디오를 수행하는 파이프라인."""

    def __init__(
        self,
        normalizer: TextNormalizer | None = None,
        phonemizer: KoreanG2PPhonemizer | None = None,
        mel_generator: MelSpectrogramGenerator | None = None,
        vocoder: SimpleVocoder | None = None,
    ) -> None:
        self.normalizer = normalizer or TextNormalizer()
        self.phonemizer = phonemizer or KoreanG2PPhonemizer()
        self.mel_generator = mel_generator or VITSMelSpectrogramGenerator()
        self.vocoder = vocoder or SimpleVocoder()

    def synthesize(self, text: str) -> TTSSample:
        normalized = self.normalizer.normalize(text)
        phonemes = self.phonemizer.to_phonemes(normalized)
        mel_result: MelOutput = self.mel_generator.generate(phonemes, text=normalized)
        mel = mel_result.mel
        audio = mel_result.audio
        sample_rate = mel_result.sample_rate

        if audio is None:
            if mel is None:
                raise ValueError("mel_generator가 mel/audio 모두 생성하지 못했습니다.")
            audio = self.vocoder.mel_to_audio(mel)
            sample_rate = self.vocoder.config.sample_rate

        return TTSSample(
            text=text,
            normalized_text=normalized,
            phonemes=phonemes,
            mel=mel,
            audio=audio,
            sample_rate=sample_rate,
        )

    def save_audio(self, sample: TTSSample, path: str | Path) -> Path:
        return self.vocoder.save_wav(sample.audio, path, sample.sample_rate)

    def dump_metadata(self, sample: TTSSample) -> dict:
        return {
            "text": sample.text,
            "normalized_text": sample.normalized_text,
            "phonemes": sample.phonemes,
            "mel_shape": sample.mel.shape if sample.mel is not None else None,
            "audio_samples": len(sample.audio),
            "sample_rate": sample.sample_rate,
        }

