import msgspec

import cgt_ai_core.tts_enums as tts


class AudioMessage(msgspec.Struct):
    channels: int
    sample_rate: int
    samples: bytes


class SpeechRecognitionMessage(msgspec.Struct):
    language: str
    language_probability: float
    text: str


class TTSRequestMessage(msgspec.Struct):
    language: tts.Language
    voice: tts.Voice
    text: str
