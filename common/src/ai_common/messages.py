import msgspec
import numpy as np

import ai_common.enums.actor_commands as ac
import ai_common.enums.tts as tts
import ai_common.enums.notifications as notifications


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
