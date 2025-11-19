# Lab / TTS

간단하지만 각 단계를 개별 클래스로 분리한 TTS 실험 폴더입니다.  
목표는 “텍스트 정규화 → 발음/phoneme → mel-spectrogram → vocoder” 파이프라인을 눈으로 확인하고, 필요 시 각 단계를 쉽게 교체할 수 있도록 하는 것입니다.

## 폴더 구조

```
lab/tts
├── __init__.py
├── demo.py
├── normalizer.py
├── phonemizer.py
├── mel_generator.py
├── pipeline.py
├── vocoder.py
└── READMD.md
```

각 파일은 단일 책임을 가지며, `TTSPipeline` 클래스가 전체 플로우를 조립합니다.

## 빠른 실행

```
python -m pip install -r lab/tts/requirements.txt
python -m lab.tts.demo --text "안녕하세요. 모듈형 TTS입니다."
```

처음 실행하면 Hugging Face Hub에서 `tts_models/ko/kss/vits` 모델과 가중치를 자동으로 다운로드합니다.  
결과물:
- `lab/tts/output/sample.wav`: VITS 모델이 합성한 한국어 음성
- `lab/tts/output/metadata.json`: 정규화 텍스트, phoneme 시퀀스, 샘플레이트 등의 로그

### 주요 CLI 옵션

```
python -m lab.tts.demo \
  --text "스타일을 바꿔보자" \
  --vits-model tts_models/ko/kss/vits \
  --speaker default \
  --speed 0.95 \
  --use-cuda
```

- `--vits-model`: Hugging Face 모델 이름이나 로컬 체크포인트 경로
- `--speaker`: 멀티 스피커 모델에서 사용할 화자 id/name
- `--speed`: 발화 속도(기본 1.0). 0.9는 조금 느리고 1.1은 빠르게 들립니다.
- `--use-cuda`: GPU가 있다면 CUDA로 추론

## 컴포넌트 갈아끼우기

- `TextNormalizer`: 표준 라이브러리 기반 간단한 정규화
- `KoreanG2PPhonemizer`: `g2pk`로 한글을 음소 시퀀스로 변환 (필요 시 다른 g2p로 교체)
- `VITSMelSpectrogramGenerator`: Coqui TTS의 VITS 모델을 로드해 직접 오디오를 생성 (Tacotron2+HiFi-GAN 등으로 바꿀 수 있도록 mock generator도 유지)
- `SimpleVocoder`: mel만 들어오는 경우를 대비한 기본 vocoder (Griffin-Lim, HiFi-GAN 등으로 대체 가능)

`TTSPipeline` 생성 시 원하는 객체를 주입하면 됩니다.

```python
from lab.tts import (
    TTSPipeline,
    TextNormalizer,
    KoreanG2PPhonemizer,
    VITSMelSpectrogramGenerator,
    VITSGeneratorConfig,
)

pipeline = TTSPipeline(
    normalizer=TextNormalizer(),
    phonemizer=KoreanG2PPhonemizer(),
    mel_generator=VITSMelSpectrogramGenerator(
        VITSGeneratorConfig(model_name="tts_models/ko/kss/vits")
    ),
)
```
