import msgspec


class AudioCaptureMessage(msgspec.Struct):
    channels: int
    sample_rate: int
    samples: bytes


class SpeechRecognitionMessage(msgspec.Struct):
    language: str
    language_probability: float
    text: str
