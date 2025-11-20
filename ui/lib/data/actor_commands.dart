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

enum Voice {
  American_Male_Adam,
  American_Male_Echo,
  American_Male_Eric,
  American_Male_Fenrir,
  American_Male_Liam,
  American_Male_Michael,
  American_Male_Onyx,
  American_Male_Puck,
  American_Male_Santa,
  American_Female_Heart,
  American_Female_Alloy,
  American_Female_Aoede,
  American_Female_Bella,
  American_Female_Jessica,
  American_Female_Kore,
  American_Female_Nicole,
  American_Female_Nova,
  American_Female_River,
  American_Female_Sarah,
  American_Female_Sky,
  British_Male_Daniel,
  British_Male_Fable,
  British_Male_George,
  British_Male_Lewis,
  British_Female_Alice,
  British_Female_Emma,
  British_Female_Isabella,
  British_Female_Lily,
  Spanish_Male_Alex,
  Spanish_Male_Santa,
  Spanish_Female_Dora,
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
  final Voice voice;
  final Actor actor;
  final List<Command> commands;

  ActorCommands({
    required this.voice,
    required this.actor,
    required this.commands,
  });
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
          voice: Voice.American_Male_Onyx,
          commands: [
            Command(
              action: Action.drive,
              reply: "Roger, driving!",
              label: "Start driving",
            ),
            Command(
              action: Action.halt,
              reply: "Roger, stopping!",
              label: "Stop driving",
            ),
          ],
        ),
        ActorCommands(
          actor: Actor.gunner,
          voice: Voice.American_Male_Onyx,
          commands: [
            Command(
              action: Action.fire,
              reply: "Roger. Firing!",
              label: "Start firing",
            ),
            Command(
              action: Action.cease_fire,
              reply: "Roger. Ceasing fire!",
              label: "Stop firing",
            ),
            Command(
              action: Action.target_twelve_o_clock,
              reply: "Roger. Engaging target, twelve o'clock!",
              label: "Target is at twelve o'clock.",
            ),
            Command(
              action: Action.target_three_o_clock,
              reply: "Roger. Engaging target, three o'clock!",
              label: "Target is at three o'clock.",
            ),
            Command(
              action: Action.target_six_o_clock,
              reply: "Roger. Engaging target, six o'clock!",
              label: "Target is at six o'clock.",
            ),
            Command(
              action: Action.target_nine_o_clock,
              reply: "Roger. Engaging target, nine o'clock!",
              label: "Target is at nine o'clock.",
            ),
          ],
        ),
      ],
    );
  }
}
