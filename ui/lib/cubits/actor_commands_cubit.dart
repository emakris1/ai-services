import 'package:app/data/actor_commands.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:app/data/repo/actor_commands_repo.dart';
import 'package:app/messaging/rabbitmq_producer.dart';

class ActorCommandsState {
  final CommandConfig config;
  final Actor? selectedActor;
  final Action? selectedAction;
  final String? selectedPhrase;

  ActorCommandsState({
    required this.config,
    this.selectedActor,
    this.selectedAction,
    this.selectedPhrase,
  });

  ActorCommandsState copyWith({
    CommandConfig? config,
    Actor? selectedActor,
    Action? selectedAction,
    String? selectedPhrase,
  }) {
    return ActorCommandsState(
      config: config ?? this.config,
      selectedActor: selectedActor ?? this.selectedActor,
      selectedAction: selectedAction ?? this.selectedAction,
      selectedPhrase: selectedPhrase ?? this.selectedPhrase,
    );
  }
}

class ActorCommandsCubit extends Cubit<ActorCommandsState> {
  final ActorCommandsRepo repo = ActorCommandsRepo(
    fileLocation: 'assets/commands.json',
  );
  final RabbitMQProducer producer = RabbitMQProducer(
    exchangeName: "actor_commands",
    routingKey: "actor_commands_service",
  );

  ActorCommandsCubit()
    : super(
        ActorCommandsState(
          config: CommandConfig(lastModified: DateTime.now(), commands: []),
          selectedActor: null,
          selectedAction: null,
          selectedPhrase: null,
        ),
      ) {
    _init();
  }

  Future<void> _init() async {
    producer.init();
    final config = await repo.load();
    final firstActor = config.commands.isNotEmpty
        ? config.commands.first.actor
        : null;
    final firstAction =
        firstActor != null && config.commands.first.commands.isNotEmpty
        ? config.commands.first.commands.first.action
        : null;
    final firstPhrase = firstActor != null && firstAction != null
        ? config.commands.first.commands.first.phrases.firstOrNull
        : null;

    emit(
      ActorCommandsState(
        config: config,
        selectedActor: firstActor,
        selectedAction: firstAction,
        selectedPhrase: firstPhrase,
      ),
    );
  }

  void _update(CommandConfig newConfig) async {
    emit(state.copyWith(config: newConfig));
    await repo.save(newConfig);
  }

  void selectActor(Actor actor) {
    final actorCmd = state.config.commands.firstWhere((a) => a.actor == actor);
    final firstAction = actorCmd.commands.first.action;
    final firstPhrase = actorCmd.commands.first.phrases.firstOrNull;
    emit(
      state.copyWith(
        selectedActor: actor,
        selectedAction: firstAction,
        selectedPhrase: firstPhrase,
      ),
    );
  }

  void selectAction(Action action) {
    emit(state.copyWith(selectedAction: action, selectedPhrase: null));
  }

  void selectPhrase(String phrase) {
    emit(state.copyWith(selectedPhrase: phrase));
  }

  void addPhrase(Actor actor, Action action, String newPhrase) {
    final updatedConfig = _modifyCommand(actor, action, (cmd) {
      cmd.phrases = [...cmd.phrases, newPhrase];
    });
    _update(updatedConfig);
  }

  void updatePhrase(Actor actor, Action action, int index, String newPhrase) {
    final updatedConfig = _modifyCommand(actor, action, (cmd) {
      if (index >= 0 && index < cmd.phrases.length) {
        final newPhrases = List<String>.from(cmd.phrases);
        newPhrases[index] = newPhrase;
        cmd.phrases = newPhrases;
      }
    });
    _update(updatedConfig);
  }

  void removePhrase(Actor actor, Action action, int index) {
    final updatedConfig = _modifyCommand(actor, action, (cmd) {
      if (index >= 0 && index < cmd.phrases.length) {
        final newPhrases = List<String>.from(cmd.phrases)..removeAt(index);
        cmd.phrases = newPhrases;
      }
    });
    _update(updatedConfig);
  }

  void updateReply(Actor actor, Action action, String newReply) {
    final updatedConfig = _modifyCommand(actor, action, (cmd) {
      cmd.reply = newReply;
    });
    _update(updatedConfig);
  }

  CommandConfig _modifyCommand(
    Actor actor,
    Action action,
    void Function(Command cmd) modify,
  ) {
    final updatedCommands = state.config.commands.map((actorCmd) {
      if (actorCmd.actor == actor) {
        final newCmds = actorCmd.commands.map((cmd) {
          if (cmd.action == action) {
            final updatedCmd = Command(
              action: cmd.action,
              reply: cmd.reply,
              phrases: List<String>.from(cmd.phrases),
            );
            modify(updatedCmd);
            return updatedCmd;
          }
          return cmd;
        }).toList();
        return ActorCommands(actor: actorCmd.actor, commands: newCmds);
      }
      return actorCmd;
    }).toList();

    return CommandConfig(
      lastModified: DateTime.now(),
      commands: updatedCommands,
    );
  }

  void publishMappings() {
    final message = repo.toDomain(state.config);
    producer.publish(message);
  }
}
