from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pipeline import TTSPipeline
from .mel_generator import VITSMelSpectrogramGenerator, VITSGeneratorConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="간단한 모듈형 TTS 데모")
    parser.add_argument("--text", type=str, required=True, help="합성할 문장")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("lab/tts/output"),
        help="생성된 오디오를 저장할 디렉터리",
    )
    parser.add_argument(
        "--filename",
        type=str,
        default="sample.wav",
        help="저장할 wav 파일 이름",
    )
    parser.add_argument(
        "--metadata",
        type=str,
        default="metadata.json",
        help="중간 산출물을 덤프할 json 파일",
    )
    parser.add_argument(
        "--vits-model",
        type=str,
        default="tts_models/ko/kss/vits",
        help="Coqui TTS 모델 이름 또는 로컬 경로",
    )
    parser.add_argument(
        "--speaker",
        type=str,
        default=None,
        help="멀티 스피커 모델에서 선택할 speaker id/name",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="발화 속도 조절 계수 (1.0이 기본)",
    )
    parser.add_argument(
        "--use-cuda",
        action="store_true",
        help="가능하면 CUDA(GPU)로 추론",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    mel_generator = VITSMelSpectrogramGenerator(
        VITSGeneratorConfig(
            model_name=args.vits_model,
            speaker=args.speaker,
            use_cuda=args.use_cuda,
            speed=args.speed,
        )
    )
    pipeline = TTSPipeline(mel_generator=mel_generator)
    sample = pipeline.synthesize(args.text)

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    audio_path = output_dir / args.filename
    pipeline.save_audio(sample, audio_path)

    metadata_path = output_dir / args.metadata
    metadata_path.write_text(
        json.dumps(pipeline.dump_metadata(sample), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"[+] Audio saved to: {audio_path}")
    print(f"[+] Metadata saved to: {metadata_path}")


if __name__ == "__main__":
    main()

