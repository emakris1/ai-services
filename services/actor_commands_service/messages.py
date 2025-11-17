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
    TARGET_TWELVE_O_CLOCK = 4
    TARGET_THREE_O_CLOCK = 5
    TARGET_SIX_O_CLOCK = 6
    TARGET_NINE_O_CLOCK = 7


class Command(msgspec.Struct):
    action: Action
    reply: str
    label: str


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


class CurrentActorMessage(msgspec.Struct):
    actor: Actor
