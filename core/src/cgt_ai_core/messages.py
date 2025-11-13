import msgspec


class AudioCaptureMessage(msgspec.Struct):
    channels: int
    sample_rate: int
    samples: bytes


class SpeechRecognitionMessage(msgspec.Struct):
    language: str
    language_probability: float
    text: str


class TTSRequestMessage(msgspec.Struct):
    voice: str
    text: str


class TTSResponseMessage(msgspec.Struct):
    sample_rate: int
    speech: bytes
