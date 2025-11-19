from __future__ import annotations

import math
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np


@dataclass
class VocoderConfig:
    sample_rate: int = 22050
    hop_length: int = 256
    amplitude: float = 0.25
    min_freq: float = 110.0
    max_freq: float = 320.0
    harmonics: tuple[float, ...] = (1.0, 2.0, 3.1)
    attack_portion: float = 0.15
    release_portion: float = 0.15


class SimpleVocoder:
    """mel-spectrogram을 간단한 sine 합성으로 wav로 변환."""

    def __init__(self, config: VocoderConfig | None = None) -> None:
        self.config = config or VocoderConfig()

    def mel_to_audio(self, mel: np.ndarray) -> np.ndarray:
        if mel.size == 0:
            return np.zeros(1, dtype=np.float32)

        hop = self.config.hop_length
        sr = self.config.sample_rate

        mel = np.maximum(mel, 0.0)
        mel_norm = mel / (np.max(mel) + 1e-6)
        energies = np.mean(mel_norm, axis=1)
        bins = np.arange(mel.shape[1])
        centroids = np.sum(mel_norm * bins, axis=1) / (np.sum(mel_norm, axis=1) + 1e-6)
        freq_ratios = centroids / (mel.shape[1] - 1 + 1e-6)
        freqs = self.config.min_freq + freq_ratios * (self.config.max_freq - self.config.min_freq)

        attack = max(1, int(hop * self.config.attack_portion))
        release = max(1, int(hop * self.config.release_portion))
        envelope = np.ones(hop, dtype=np.float32)
        envelope[:attack] = np.linspace(0.0, 1.0, attack, dtype=np.float32)
        envelope[-release:] = np.linspace(1.0, 0.0, release, dtype=np.float32)

        samples = np.zeros(len(freqs) * hop, dtype=np.float32)
        phases = np.zeros(len(self.config.harmonics), dtype=np.float64)

        for frame_idx, (freq, energy) in enumerate(zip(freqs, energies)):
            base_amp = self.config.amplitude * (0.3 + energy)
            for n in range(hop):
                sample = 0.0
                for h_idx, harmonic in enumerate(self.config.harmonics):
                    phases[h_idx] += 2 * math.pi * freq * harmonic / sr
                    sample += math.sin(phases[h_idx]) / harmonic
                idx = frame_idx * hop + n
                samples[idx] = sample * base_amp * envelope[n]

        noise = np.random.default_rng(42).normal(0, 0.003, size=samples.shape)
        samples = np.clip(samples + noise, -1.0, 1.0)
        return samples.astype(np.float32)

    def save_wav(
        self, audio: Iterable[float], path: str | Path, sample_rate: int | None = None
    ) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        audio_arr = np.asarray(list(audio), dtype=np.float32)
        audio_arr = np.clip(audio_arr, -1.0, 1.0)
        int16 = (audio_arr * 32767).astype(np.int16)

        with wave.open(str(path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate or self.config.sample_rate)
            wav_file.writeframes(int16.tobytes())

        return path

