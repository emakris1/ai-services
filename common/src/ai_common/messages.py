import msgspec
import numpy as np

import ai_common.enums.tts as tts


class AudioMessage(msgspec.Struct):
    sample_rate: int
    samples: np.ndarray


class StopListeningMessage(msgspec.Struct):
    duration: float


class SpeechRecognitionMessage(msgspec.Struct):
    language: str
    language_probability: float
    text: str


class TTSRequestMessage(msgspec.Struct):
    language: tts.Language
    voice: tts.Voice
    text: str

