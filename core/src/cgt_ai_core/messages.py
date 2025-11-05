import msgspec


class AudioCaptureMessage(msgspec.Struct):
    channels: int
    sample_rate: int
    samples: bytes
