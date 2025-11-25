import os
import time
from dataclasses import dataclass

import torchaudio as ta
from chatterbox.mtl_tts import ChatterboxMultilingualTTS


# ===== 기본 설정값 =====
# 보이스 클로닝에 사용할 참조 음성(.wav)
AUDIO_PROMPT_PATH = "../dataset/wavs/karina-tts-voice-cloning.wav"

# 합성할 텍스트
TEXT = "CPSP는 빅토리아급 4척을 대체할 3000톤급 잠수함 12척을 도입하는 대규모 프로젝트로, 캐나다가 K-조선을 유력 후보군에 올려놓고 기술·산업성을 전방위로 따져보고 있음을 보여준다."

# 언어 ID (예: 한국어: \"ko\", 영어: \"en\", 일본어: \"ja\" 등)
LANGUAGE_ID = "ko"

# 출력 파일 이름
OUTPUT_PATH = "output/output.wav"

# 실행 장치: \"cpu\" / \"cuda\" 등 (환경에 맞게 직접 지정)
DEVICE = "cuda"


@dataclass
class GenerateConfig:
    exaggeration: float = 0.5
    cfg_weight: float = 0.5
    temperature: float = 0.8
    repetition_penalty: float = 2.0
    min_p: float = 0.05
    top_p: float = 1.0


# 여기 값만 바꿔 가면서 실험하면 됩니다.
GEN_CFG = GenerateConfig(
    exaggeration=0.5,
    cfg_weight=0.95,
    temperature=0.8,
    repetition_penalty=5.0,
    min_p=0.1,
    top_p=0.9,
)


def main() -> None:
    model = ChatterboxMultilingualTTS.from_pretrained(device=DEVICE)
    text = TEXT.strip()

    gen_start = time.perf_counter()
    wav = model.generate(
        text,
        language_id=LANGUAGE_ID,
        audio_prompt_path=AUDIO_PROMPT_PATH,
        exaggeration=GEN_CFG.exaggeration,
        cfg_weight=GEN_CFG.cfg_weight,
        temperature=GEN_CFG.temperature,
        repetition_penalty=GEN_CFG.repetition_penalty,
        min_p=GEN_CFG.min_p,
        top_p=GEN_CFG.top_p,
    )

    gen_end = time.perf_counter()

    output_path = OUTPUT_PATH
    sample_rate = model.sr

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    ta.save(output_path, wav, sample_rate)
    total_end = time.perf_counter()

    print(f"[측정] 합성 시간: {gen_end - gen_start:.3f}초, 저장 포함 총 시간: {total_end - gen_start:.3f}초")


if __name__ == "__main__":
    main()

