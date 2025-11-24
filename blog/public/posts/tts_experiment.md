## TTS 모듈 구현 기록

이것저것 시도는 많이 하는 편이라고 생각하는데 기록으로 남겨놓는 것은 적다보니 간단한 구현도 기록으로 남겨볼 생각이다. 개인적으로 만들고 있는 앱에서 TTS를 넣어보고 싶어서 조금 건들여 보았다. Pytorch로 직접 모델을 불러와 해볼 수도 있지만 Coqui TTS를 사용해보기로 했다. 

### Coqui TTS
- 오픈소스 텍스트-음성 변환(Text-to-Speech, TTS) 프레임워크
- 여러 모델 구조(예: Tacotron2, FastSpeech, VITS 등)를 지원하며, 다양한 언어/데이터셋으로 학습 가능

~~~
from TTS.api import TTS

# 기본 영어 모델로 테스트
tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
tts.tts_to_file(text="Hello world. This is a test.", file_path="output.wav")
~~~

우리가 흔히 아는 딱딱한 TTS 음성의 영어 음성이 생성되는 것을 확인했다. 다음은 다국어 모델인 XTTS-v2를 사용하여 한국어 음성을 생성해보았다.

~~~
import os
import torch
from TTS.api import TTS

os.environ["COQUI_TOS_AGREED"] = "1"

device = "cuda" if torch.cuda.is_available() else "cpu"
tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2").to(device)

# XTTS-v2 테스트
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
~~~

XTTS-v2 보이스 클로닝을 제공하는데 짧은 음성 샘플(speaker_wav)을 입력받아 목소리와 말투를 모사하는 기술이다. 파라미터와 speacker 보이스를 바꿔가며 테스트를 진행해보았을 때 다음과 같은 문제점을 파악했다. 

- **어눌함, 말투와 같은 품질 문제:** 일단 XTTS-v2의 경우 샘플 음성의 길이, 품질에 많은 영향을 받는 것을 확인했다. 품질이 높고 길이가 길수록 말투가 많이 보완되는 것을 확인했다. 그러나 늘어지는 발음, 억양 등이 다소 어색한 것은 완전히 고쳐지지 않았다.

    Coqui TTS는 파인 튜닝을 지원하므로 한국어 음성으로 파인 튜닝을 해보고 어느정도까지 품질 문제가 개선되는지 확인해봐야 할 것 같다.

- **텍스트 전처리 부재:**  XTTS-v2가 언어를 지정하고 생성하기 때문에 발생하는 문제로 보이는데 한글 사이에 영어가 포함되어 있을 때 영어를 제대로 읽지 못 했다. 또한 상황에 따라 다르게 읽어야 하는 경우 역시 완벽하게 캐치하지 못 했다. 

    예를 들면, Samsung의 경우 그대로 삼성이라고 읽지만 KT의 경우 약자이므로 케이티라고 읽는다. 숫자도 1950m는 그대로 천구백오십미터라고 읽지만 학번이나 군번의 경우 번호를 순서대로 불러서 읽는다. 이러한 차이를 구분하지 못하기 때문에 TTS 앞단에 텍스트를 전처리해줄 모듈이 필요해보인다. 
