"""
Coqui TTS 기본 테스트
"""

from TTS.api import TTS

# 영어 모델로 테스트
tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
tts.tts_to_file(text="Hello world. This is a test.", file_path="output.wav")
