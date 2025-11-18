enum Actor { driver, gunner }

enum Action {
  drive,
  halt,
  fire,
  cease_fire,
  target_twelve_o_clock,
  target_three_o_clock,
  target_six_o_clock,
  target_nine_o_clock,
}

typedef Reply = String;
typedef Phrase = String;

class Command {
  final Action action;
  Reply reply;
  String label;

  Command({required this.action, required this.reply, required this.label});

  static Command empty(Action action) {
    return Command(action: action, reply: "", label: "");
  }
}

class ActorCommands {
  final Actor actor;
  final List<Command> commands;

  ActorCommands({required this.actor, required this.commands});
}

class CommandConfig {
  final DateTime lastModified;
  final List<ActorCommands> commands;

  CommandConfig({required this.lastModified, required this.commands});

  static CommandConfig empty() {
    return CommandConfig(
      lastModified: DateTime.now(),
      commands: [
        ActorCommands(
          actor: Actor.driver,
          commands: [Command.empty(Action.drive), Command.empty(Action.halt)],
        ),
        ActorCommands(
          actor: Actor.gunner,
          commands: [
            Command.empty(Action.fire),
            Command.empty(Action.cease_fire),
            Command.empty(Action.target_twelve_o_clock),
            Command.empty(Action.target_three_o_clock),
            Command.empty(Action.target_six_o_clock),
            Command.empty(Action.target_nine_o_clock),
          ],
        ),
      ],
    );
  }
}
