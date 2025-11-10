import msgspec
import enum

class Actor(enum.Enum):
    DRIVER = 'driver'
    GUNNER = 'gunner'

class Action(enum.Enum):
    DRIVE = 'drive'
    HALT = 'halt'
    FIRE = 'fire'
    CEASE_FIRE = 'cease_fire'
    UNKNOWN = 'unknown'

class Command(msgspec.Struct):
    action: Action
    reply: str
    phrases: list[str]

class ActorCommands(msgspec.Struct):
    actor: Actor
    commands: list[Command]

class CommandConfig(msgspec.Struct):
    last_modified: str
    commands: list[ActorCommands]

def dict_to_command_config(data: dict) -> CommandConfig:
    return CommandConfig(
        last_modified=data["last_modified"],
        commands=[
            ActorCommands(
                actor=Actor(actor_data["actor"]),
                commands=[
                    Command(
                        action=Action(cmd_data["action"]),
                        reply=cmd_data["reply"],
                        phrases=cmd_data["phrases"],
                    )
                    for cmd_data in actor_data["commands"]
                ],
            )
            for actor_data in data["commands"]
        ],
    )

class ActionRecognitionMessage(msgspec.Struct):
    score: float
    actor: Actor
    action: Action