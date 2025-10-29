import msgspec


class SpeechCaptureMessage(msgspec.Struct):
    channels: int
    sample_rate: int
    samples: bytes
