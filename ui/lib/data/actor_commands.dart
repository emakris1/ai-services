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

  static CommandConfig initial() {
    return CommandConfig(
      lastModified: DateTime.now(),
      commands: [
        ActorCommands(
          actor: Actor.driver,
          commands: [
            Command(
              action: Action.drive,
              reply: "Roger, driving!",
              label: "drive",
            ),
            Command(
              action: Action.halt,
              reply: "Roger, stopping!",
              label: "stop driving",
            ),
          ],
        ),
        ActorCommands(
          actor: Actor.gunner,
          commands: [
            Command(
              action: Action.fire,
              reply: "Roger. Firing!",
              label: "a command telling a gunner to start firing",
            ),
            Command(
              action: Action.cease_fire,
              reply: "Roger. ceasing fire!",
              label: "a command telling a gunner to stop firing",
            ),
            Command(
              action: Action.target_twelve_o_clock,
              reply: "Roger. Engaging target, twelve o clock!",
              label: "target is at twelve o clock",
            ),
            Command(
              action: Action.target_three_o_clock,
              reply: "Roger. Engaging target, three o clock!",
              label: "target is at three o clock",
            ),
            Command(
              action: Action.target_six_o_clock,
              reply: "Roger. Engaging target, six o clock!",
              label: "target is at six o clock",
            ),
            Command(
              action: Action.target_nine_o_clock,
              reply: "Roger. Engaging target, nine o clock!",
              label: "target is at nine o clock",
            ),
          ],
        ),
      ],
    );
  }
}
