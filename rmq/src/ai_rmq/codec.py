import base64
import numpy as np

from typing import Any, Type


def enc_hook(obj: Any) -> Any:
    if isinstance(obj, np.ndarray):
        return obj.shape, obj.tobytes()
    else:
        raise NotImplementedError(f'Object of type {type(obj)} is not supported')

def dec_hook(obj_type: Type, obj: Any):
    if obj_type is np.ndarray:
        shape, buffer = obj
        # msgspec JSON-encodes the raw bytes from enc_hook as base64, so they arrive here as a base64 string
        return np.frombuffer(buffer=base64.b64decode(buffer), dtype=np.float32).reshape(shape)
    else:
        raise NotImplementedError(f'Object of type {obj_type} is not supported')
