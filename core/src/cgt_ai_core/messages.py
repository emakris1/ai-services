import base64
import msgspec
import numpy as np

from typing import Any, Type

import cgt_ai_core.actor_command_enums as ac
import cgt_ai_core.tts_enums as tts
import cgt_ai_core.notification_enums as notifications


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
    cache_speech: bool = True
    play_immediately: bool = True


class Command(msgspec.Struct):
    action: ac.Action
    reply: str
    label: str


class ActorCommands(msgspec.Struct):
    actor: ac.Actor
    voice: int
    commands: list[Command]


class CommandConfigMessage(msgspec.Struct):
    last_modified: str
    commands: list[ActorCommands]


class ActionRecognitionMessage(msgspec.Struct):
    score: float
    actor: ac.Actor
    action: ac.Action


class CurrentActorMessage(msgspec.Struct):
    actor: ac.Actor


class NotificationMessage(msgspec.Struct):
    icon: notifications.Icon
    title: str
    message: str
    color: notifications.Color


def enc_hook(obj: Any) -> Any:
    if isinstance(obj, np.ndarray):
        return obj.shape, obj.tobytes()
    else:
        raise NotImplementedError(f'Object of type {type(obj)} is not supported')

def dec_hook(obj_type: Type, obj: Any):
    if obj_type is np.ndarray:
        shape, buffer = obj
        return np.frombuffer(buffer=base64.b64decode(buffer), dtype=np.float32).reshape(shape)
    else:
        raise NotImplementedError(f'Object of type {obj_type} is not supported')
