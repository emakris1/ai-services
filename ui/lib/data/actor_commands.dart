enum Actor { driver, gunner }

enum Action { drive, halt, fire, cease_fire }

typedef Reply = String;
typedef Phrase = String;

class Command {
  final Action action;
  Reply reply;
  List<Phrase> phrases;

  Command({required this.action, required this.reply, required this.phrases});
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
}
