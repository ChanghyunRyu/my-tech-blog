import os
import torch
from TTS.api import TTS

os.environ["COQUI_TOS_AGREED"] = "1"

device = "cuda" if torch.cuda.is_available() else "cpu"
tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2").to(device)

# XTTS-v2 파라미터 테스트
tts.tts_to_file(
    text="안녕하세요. 오늘은 날씨가 좋네요. 아이 캔 스피크 잉글리쉬.",
    language="ko",
    speaker_wav="output/output.wav",
    file_path="output/test_params.wav",
    
    # 제어 가능한 파라미터들
    temperature=0.65,           # 0.0~1.0, 낮을수록 안정적, 높을수록 다양함 (기본: 0.85)
    length_penalty=0.5,        # 길이 페널티 (기본: 1.0)
    repetition_penalty=7.0,    # 반복 방지 (기본: 2.0, 높을수록 반복 적음)
    top_k=50,                  # Top-K 샘플링 (기본: 50)
    top_p=0.85,                # Top-P 샘플링 (기본: 0.85)
    speed=2,                 # 속도 조절 (기본: 1.0)
    enable_text_splitting=False # 문장 분할 여부 (기본: True)
)

print("완료: output/test_params.wav")