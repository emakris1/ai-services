import msgspec
import enum


class Actor(enum.Enum):
    DRIVER = 0
    GUNNER = 1


class Action(enum.Enum):
    UNKNOWN = -1
    DRIVE = 0
    HALT = 1
    FIRE = 2
    CEASE_FIRE = 3


class Command(msgspec.Struct):
    action: Action
    reply: str
    phrases: list[str]


class ActorCommands(msgspec.Struct):
    actor: Actor
    commands: list[Command]


class CommandConfigMessage(msgspec.Struct):
    last_modified: str
    commands: list[ActorCommands]


class ActionRecognitionMessage(msgspec.Struct):
    score: float
    actor: Actor
    action: Action
