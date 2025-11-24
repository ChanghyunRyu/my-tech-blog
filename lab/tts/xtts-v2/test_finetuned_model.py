"""
XTTS-v2 파인튜닝 모델 테스트 (간편 API)
"""
import torch
import torchaudio
import os
from pathlib import Path
from dataclasses import dataclass

# TTS 모듈 임포트
import sys
sys.path.insert(0, str(Path("xtts_finetune_repo/TTS").resolve()))

from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts


@dataclass
class TTSParams:
    """TTS 생성 파라미터
    
    주요 파라미터:
    - temperature: 0.1~1.0 (낮을수록 안정적, 높을수록 다양함)
    - top_p: 0.3~0.95 (샘플링 범위)
    - top_k: 상위 K개 토큰만 고려
    - length_penalty: 낮을수록 길어짐 (0.5=길게, 1.0=중립, 2.0=짧게) ⚠️
    - repetition_penalty: 2.0~7.0 (높을수록 반복 적음, 너무 높으면 조기 종료)
    - do_sample: True=샘플링, False=greedy
    - speed: 0.5~2.0 (속도 조절, 1.0=기본)
    - min_length: 최소 생성 토큰 수 (길이 보장) ⭐
    - max_new_tokens: 최대 생성 토큰 수
    """
    # 기본 샘플링 파라미터
    temperature: float = 0.7
    top_p: float = 0.85
    top_k: int = 50
    
    # 길이 조절 파라미터
    length_penalty: float = 1.0      # ⚠️ 낮을수록 길게 생성!
    repetition_penalty: float = 5.0
    min_length: int = None           # ⭐ 최소 토큰 수 (None=제한 없음)
    max_new_tokens: int = None       # 최대 토큰 수 (None=기본값 사용)
    
    # 고급 옵션
    do_sample: bool = True
    speed: float = 1.0
    enable_text_splitting: bool = False
    
    def __str__(self):
        parts = [
            f"temp={self.temperature}",
            f"top_p={self.top_p}",
            f"len_penalty={self.length_penalty}",
            f"rep_penalty={self.repetition_penalty}",
        ]
        if self.min_length is not None:
            parts.append(f"min_len={self.min_length}")
        if self.speed != 1.0:
            parts.append(f"speed={self.speed}")
        return f"TTSParams({', '.join(parts)})"


# 모델 경로 설정
CHECKPOINT_DIR = Path("checkpoints/GPT_XTTS_FT-November-25-2025_12+17AM-8e59ec3")
CHECKPOINT_PATH = CHECKPOINT_DIR / "checkpoint_4000.pth"
CONFIG_PATH = CHECKPOINT_DIR / "config.json"
VOCAB_PATH = Path("checkpoints/XTTS_v2.0_original_model_files/vocab.json")

# 출력 경로
OUTPUT_DIR = Path("output_finetuned")
OUTPUT_DIR.mkdir(exist_ok=True)

def load_finetuned_model():
    """파인튜닝된 모델 로드"""
    print("=" * 60)
    print("파인튜닝된 XTTS-v2 모델 로딩...")
    print("=" * 60)
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")
    
    # Config 로드
    print(f"\n[1/3] Config 로드: {CONFIG_PATH}")
    config = XttsConfig()
    config.load_json(str(CONFIG_PATH))
    
    # 모델 초기화
    print(f"[2/3] 모델 초기화...")
    model = Xtts.init_from_config(config)
    
    # 체크포인트 로드
    print(f"[3/3] 체크포인트 로드: {CHECKPOINT_PATH}")
    model.load_checkpoint(
        config,
        checkpoint_dir=str(CHECKPOINT_DIR),
        checkpoint_path=str(CHECKPOINT_PATH),
        vocab_path=str(VOCAB_PATH),
        use_deepspeed=False
    )
    
    model.to(device)
    print("\n✅ 파인튜닝 모델 로드 완료!\n")
    
    return model, config, device


def load_original_model():
    """원본 XTTS-v2 모델 로드 (파인튜닝 안 된 버전)"""
    print("=" * 60)
    print("원본 XTTS-v2 모델 로딩...")
    print("=" * 60)
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")
    
    # TTS API로 원본 모델 로드
    from TTS.api import TTS
    
    print("\n원본 XTTS-v2 다운로드/로드 중...")
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
    
    print("✅ 원본 모델 로드 완료!\n")
    
    return tts, device


def generate_speech_finetuned(
    model, 
    config, 
    device, 
    text: str,
    reference_audio_path: Path,
    output_path: Path,
    params: TTSParams = None
):
    """
    파인튜닝 모델로 음성 생성
    
    Args:
        model: 로드된 XTTS 모델
        config: 모델 config
        device: 디바이스 (cuda/cpu)
        text: 생성할 텍스트
        reference_audio_path: 보이스 클로닝에 사용할 참조 오디오 경로
        output_path: 저장할 파일 경로
        params: TTS 파라미터 (None이면 기본값 사용)
    
    Returns:
        저장된 파일 경로
    """
    if params is None:
        params = TTSParams()
    
    print(f"\n{'='*60}")
    print(f"[파인튜닝 모델] 텍스트: {text}")
    print(f"참조 오디오: {reference_audio_path.name}")
    print(f"파라미터: {params}")
    print(f"{'='*60}\n")
    
    # Speaker conditioning 추출 (보이스 클로닝)
    print("Speaker embedding 추출 중...")
    gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(
        audio_path=str(reference_audio_path),
        gpt_cond_len=config.gpt_cond_len,
        max_ref_length=config.max_ref_len,
        sound_norm_refs=config.sound_norm_refs,
    )
    
    # 음성 생성
    print("음성 생성 중...")
    
    # HuggingFace generate kwargs 준비
    hf_generate_kwargs = {}
    if params.min_length is not None:
        hf_generate_kwargs['min_length'] = params.min_length
    if params.max_new_tokens is not None:
        hf_generate_kwargs['max_new_tokens'] = params.max_new_tokens
    
    out = model.inference(
        text=text,
        language="ko",
        gpt_cond_latent=gpt_cond_latent,
        speaker_embedding=speaker_embedding,
        temperature=params.temperature,
        length_penalty=params.length_penalty,
        repetition_penalty=params.repetition_penalty,
        top_k=params.top_k,
        top_p=params.top_p,
        do_sample=params.do_sample,
        speed=params.speed,
        enable_text_splitting=params.enable_text_splitting,
        **hf_generate_kwargs,
    )
    
    # 저장
    wav = torch.tensor(out["wav"]).unsqueeze(0)
    torchaudio.save(str(output_path), wav, 24000)
    
    # 길이 정보 출력
    duration = len(wav[0]) / 24000  # 샘플 수 / 샘플링 레이트
    print(f"✅ 저장 완료: {output_path}")
    print(f"   길이: {duration:.2f}초\n")
    
    return output_path


def generate_speech_original(
    tts,
    device,
    text: str,
    reference_audio_path: Path,
    output_path: Path,
    params: TTSParams = None
):
    """
    원본 모델로 음성 생성
    
    Args:
        tts: TTS API 객체
        device: 디바이스 (cuda/cpu)
        text: 생성할 텍스트
        reference_audio_path: 보이스 클로닝에 사용할 참조 오디오 경로
        output_path: 저장할 파일 경로
        params: TTS 파라미터 (None이면 기본값 사용)
    
    Returns:
        저장된 파일 경로
    """
    if params is None:
        params = TTSParams()
    
    print(f"\n{'='*60}")
    print(f"[원본 모델] 텍스트: {text}")
    print(f"참조 오디오: {reference_audio_path.name}")
    print(f"파라미터: {params}")
    print(f"{'='*60}\n")
    
    print("음성 생성 중...")
    # TTS API 사용
    wav = tts.tts(
        text=text,
        speaker_wav=str(reference_audio_path),
        language="ko",
        temperature=params.temperature,
        length_penalty=params.length_penalty,
        repetition_penalty=params.repetition_penalty,
        top_k=params.top_k,
        top_p=params.top_p,
    )
    
    # 저장
    import numpy as np
    wav_tensor = torch.FloatTensor(wav).unsqueeze(0)
    torchaudio.save(str(output_path), wav_tensor, 24000)
    
    # 길이 정보 출력
    duration = len(wav_tensor[0]) / 24000
    print(f"✅ 저장 완료: {output_path}")
    print(f"   길이: {duration:.2f}초\n")
    
    return output_path


def main():
    """
    파인튜닝 모델 vs 원본 모델 비교 테스트
    
    다양한 파라미터 조합을 테스트합니다.
    """
    # 테스트 설정
    test_text = "안녕하세요. 카리나입니다."
    test_reference = Path("dataset/wavs/karina-tts-file_0900.wav")
    
    
    finetuned_model, finetuned_config, device = load_finetuned_model()
    
    generate_speech_finetuned(
        finetuned_model, finetuned_config, device,
        text=test_text,
        reference_audio_path=test_reference,
        output_path=OUTPUT_DIR / "example_finetuned.wav",
        params=TTSParams(
            temperature=0.35,        # 약간 올림 (안정성 유지하면서 표현력)
            top_p=0.65,              # 약간 올림
            repetition_penalty=3.0,  # 적절한 반복 방지
            length_penalty=0.8      # 약간 길게
        )
    )
    
    # 메모리 정리
    del finetuned_model
    torch.cuda.empty_cache()
    
    original_tts, device = load_original_model()
    
    # 원본 모델은 기본 설정으로만 테스트
    print("\n📌 [테스트 2-1] 원본 모델 (기본)")
    generate_speech_original(
        original_tts, device,
        text=test_text,
        reference_audio_path=test_reference,
        output_path=OUTPUT_DIR / "original_default.wav",
        params=TTSParams(
            temperature=0.5,
            top_p=0.6,
            repetition_penalty=7.0
        )
    )
    
    # ========================================
    # 완료 및 요약
    # ========================================
    print("\n" + "=" * 70)
    print("✅ 모든 테스트 완료!")
    print("=" * 70)
    print(f"📂 출력 폴더: {OUTPUT_DIR.absolute()}\n")
    print("파인튜닝 모델:")
    print("  - finetuned_1_default.wav       (기본 설정 - 짧게 생성)")
    print("  - finetuned_2_long_penalty.wav  (length_penalty 낮춤)")
    print("  - finetuned_3_min_length.wav    (min_length 보장)")
    print("  - finetuned_4_balanced.wav      (⭐ 추천 설정)")
    print("\n원본 모델:")
    print("  - original_default.wav          (비교용)")
    print("\n" + "=" * 70)
    print("🎧 추천: finetuned_4_balanced.wav를 먼저 들어보세요!")
    print("\n💡 파라미터 가이드:")
    print("  - length_penalty: 낮을수록 길게 (0.5~0.8 추천)")
    print("  - repetition_penalty: 3.0~5.0 (안정성과 반복방지 균형)")
    print("  - min_length: 최소 토큰 수 (80~120 추천)")
    print("  - temperature: 0.5~0.7 (안정성)")
    print("=" * 70)

if __name__ == "__main__":
    main()

