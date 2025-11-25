import os
import time

import torchaudio as ta
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

DEVICE = "cuda"

model = ChatterboxMultilingualTTS.from_pretrained(device=DEVICE)

help(model.generate)