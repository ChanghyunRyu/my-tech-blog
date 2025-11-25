## TTS 모듈 구현 기록

여러 시도를 자주 해보는 편이지만, 막상 기록으로 남기지는 않는 경우가 많아 이번에는 간단한 구현이라도 남겨보기로 했다.  
개인적으로 만들고 있는 앱에 TTS 기능을 넣어보고 싶어 조금 만져본 내용을 정리한다. Pytorch로 직접 모델을 불러와 구현할 수도 있지만, 이번에는 Coqui TTs를 사용해보기로 했다.

---

### Coqui TTS
- 오픈소스 텍스트-음성 변환(Text-to-Speech, TTS) 프레임워크
- Tacotron2, FastSpeech, VITS 등 다양한 모델 구조 지원
- 여러 언어·데이터셋 기반의 학습 가능

먼저 기본 영어 모델을 사용해 간단히 테스트해봤다.

~~~
from TTS.api import TTS

# 기본 영어 모델로 테스트
tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
tts.tts_to_file(text="Hello world. This is a test.", file_path="output.wav")
~~~

우리가 흔히 떠올리는 딱딱한 느낌의 영어 TTS 음성이 생성된다.
다음으로 다국어 모델인 XTTS-v2를 이용해 한국어 음성을 생성해보았다.

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

XTTS-v2는 짧은 샘플 음성을 기반으로 보이스 클로닝 기능을 제공한다.  
테스트를 진행하면서 다음과 같은 문제점을 확인했다.

**✔ 품질 관련 문제(어눌함, 억양 어색함 등)** 
- 샘플 음성이 길고 품질이 좋을수록 목소리 모사는 개선됨
- 그러나 늘어지는 발음, 어색한 억양은 여전히 존재
- 보이스 클로닝 품질의 한계로 보이며, 파인 튜닝을 고려할 필요가 있음

**✔ 텍스트 전처리 부재**  

언어를 지정해놓고 생성하더라도 다음과 같은 문제가 발생한다.
- 한글 문장 속 영어 단어를 자연스럽게 읽지 못함
- 맥락에 따라 다른 발음을 해야 하는 경우 제대로 처리하지 못함
    - Samsung → “삼성”
    - KT → “케이티”
    - 1950m → “천구백오십미터”
    - 학번/군번 → “일구 오공...” 식으로 읽어야 함

따라서 TTS 앞단에 텍스트 표준화/전처리 모듈이 필요하다고 판단했다.

---

### Step 1: Coqui TTS Fine-tuning 

제로샷 보이스 클로닝만으로는 한국어 TTS 품질이 만족스럽지 않았다. 다른 모델을 찾기보다는 일단 XTTS-v2를 파인튜닝해보기로 한다.

마침 XTTS-v2를 한국어로 파인 튜닝해보았다는 [블로그 글](https://bradjobs.notion.site/TTS-85a62e9706fe49a3876208f749ce8c35)이 있어 참고했다.

#### try #1 - epoch 10, LR 5e-6, 400개 샘플(37m)

- 어눌한 말투가 꽤 개선됨. 여러 번 생성하면 깔끔한 결과가 나오기 시작
- 된소리 발음 문제, 잡음 섞임 등 여전히 개선 여지 존재
- 데이터가 적었던 만큼, 샘플 수를 늘리는 게 필요하다고 판단

#### try #2 - epoch 30, LR 5e-6, 900개 샘플(67m)

- 학습 중 epoch 7부터 loss가 감소하지 않고 증가
- 데이터가 많아지면서 높은 LR로 인한 과적합이 빠르게 발생한 것으로 보임
- 최종 Eval Loss 2.71


#### try #3 - epoch 10, LR 1e-6, 900개 샘플(67m)

- LR 낮추고 epoch도 줄여 다시 실험
- epoch 10까지 지속적으로 Eval loss 감소. 최종 2.378까지 내려감
- 하지만 음성 품질은 여전히 기대치에는 미달. Loss 감소 추세를 보면 epoch을 조금 더 늘려볼 여지는 있음

#### try #4 - epoch 20, LR 1e-6, 900개 샘플(67m)

- 최종 2.28까지 내려감
- 그러나 실제 품질은 원하는 만큼 나오지 않음. 
- Loss는 계속해서 감소했던 것으로 보아 epoch을 더 높일 수도 있겠지만 크게 유의미하지는 않을 거라 판단
- 원하는 형태의 목소리에는 근접해가지만 떨림이나 잡음 등 불안정해지는 것을 확인

하루동안 시간을 썼으나 XTTS-v2로는 내가 원하는 수준에 이르기는 힘들다고 판단되어 다른 모델을 탐색하기로 결정

### Step 2: 다른 모델 탐색

- StyleTTS 2 / Kokoro TTS
- Fish speach
- ESPnet2-TTS
- atts-2-6

