import base64
import msgspec
import numpy as np

from typing import Any, Type

import cgt_ai_core.tts_enums as tts


class AudioMessage(msgspec.Struct):
    channels: int
    sample_rate: int
    samples: np.ndarray


class SpeechRecognitionMessage(msgspec.Struct):
    language: str
    language_probability: float
    text: str


class TTSRequestMessage(msgspec.Struct):
    language: tts.Language
    voice: tts.Voice
    text: str


def enc_hook(obj: Any) -> Any:
    if isinstance(obj, np.ndarray):
        return obj.ndim, obj.tobytes()
    else:
        raise NotImplementedError(f'Object of type {type(obj)} is not supported')

def dec_hook(obj_type: Type, obj: Any):
    if obj_type is np.ndarray:
        shape, buffer = obj

        # msgspec encodes bytes as base64 strings by default, so decode if necessary
        if isinstance(buffer, str):
            buffer = base64.b64decode(buffer)

        # convert raw bytes to a numpy array
        flat_buffer = np.frombuffer(buffer=buffer, dtype=np.float32)

        if shape > 1:
            # reshape the array
            frames = flat_buffer.size // shape
            shaped_buffer = flat_buffer.reshape(frames, shape)
        else:
            shaped_buffer = flat_buffer

        return shaped_buffer
    else:
        raise NotImplementedError(f'Object of type {obj_type} is not supported')
