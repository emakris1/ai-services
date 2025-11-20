import 'package:app/data/actor_commands.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:app/data/repo/actor_commands_repo.dart';
import 'package:app/messaging/rabbitmq_producer.dart';

class ActorCommandsState {
  final CommandConfig config;
  final Actor? selectedActor;
  final Action? selectedAction;
  final Voice? selectedVoice;

  ActorCommandsState({
    required this.config,
    this.selectedActor,
    this.selectedAction,
    this.selectedVoice,
  });

  ActorCommandsState copyWith({
    CommandConfig? config,
    Actor? selectedActor,
    Action? selectedAction,
    Voice? selectedVoice,
  }) {
    return ActorCommandsState(
      config: config ?? this.config,
      selectedActor: selectedActor ?? this.selectedActor,
      selectedAction: selectedAction ?? this.selectedAction,
      selectedVoice: selectedVoice ?? this.selectedVoice,
    );
  }
}

class ActorCommandsCubit extends Cubit<ActorCommandsState> {
  final ActorCommandsRepo repo = ActorCommandsRepo();
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
          selectedVoice: null,
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
    final firstVoice = config.commands.isNotEmpty
        ? config.commands.first.voice
        : null;

    emit(
      ActorCommandsState(
        config: config,
        selectedActor: firstActor,
        selectedAction: firstAction,
        selectedVoice: firstVoice,
      ),
    );
  }

  Future<void> _update(CommandConfig newConfig, {Voice? selectedVoice}) async {
    emit(
      state.copyWith(
        config: newConfig,
        selectedVoice: selectedVoice ?? state.selectedVoice,
      ),
    );
    await repo.save(newConfig);
  }

  void selectActor(Actor actor) {
    final actorCmd = state.config.commands.firstWhere((a) => a.actor == actor);
    final firstAction = actorCmd.commands.first.action;
    emit(
      state.copyWith(
        selectedActor: actor,
        selectedAction: firstAction,
        selectedVoice: actorCmd.voice,
      ),
    );
  }

  void selectAction(Action action) {
    emit(state.copyWith(selectedAction: action));
  }

  void updateReply(Actor actor, Action action, String newReply) {
    final updatedConfig = _modifyCommand(actor, action, (cmd) {
      cmd.reply = newReply;
    });
    _update(updatedConfig);
  }

  void updateLabel(Actor actor, Action action, String newLabel) {
    final updatedConfig = _modifyCommand(actor, action, (cmd) {
      cmd.label = newLabel;
    });
    _update(updatedConfig);
  }

  void updateVoice(Actor actor, Voice newVoice) {
    final updatedCommands = state.config.commands.map((actorCmd) {
      if (actorCmd.actor == actor) {
        return ActorCommands(
          voice: newVoice,
          actor: actorCmd.actor,
          commands: actorCmd.commands,
        );
      }
      return actorCmd;
    }).toList();

    final updatedConfig = CommandConfig(
      lastModified: DateTime.now(),
      commands: updatedCommands,
    );

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
              label: cmd.label,
            );
            modify(updatedCmd);
            return updatedCmd;
          }
          return cmd;
        }).toList();
        return ActorCommands(
          voice: actorCmd.voice,
          actor: actorCmd.actor,
          commands: newCmds,
        );
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
