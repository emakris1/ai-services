import 'package:app/data/repo/action_mapping_repository.dart';
import 'package:app/messaging/rabbitmq_producer.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

enum Actor { driver, gunner }

typedef Action = String;
typedef Phrase = String;

typedef ActionPhraseMap = Map<Action, List<Phrase>>;
typedef ActionMapping = Map<Actor, ActionPhraseMap>;

class ActionMappingState {
  final ActionMapping mappings;
  final Actor? selectedActor;
  final Action? selectedAction;
  final Phrase? selectedPhrase;

  ActionMappingState({
    required this.mappings,
    this.selectedActor,
    this.selectedAction,
    this.selectedPhrase,
  });

  ActionMappingState copyWith({
    ActionMapping? mappings,
    Actor? selectedActor,
    Action? selectedAction,
    Phrase? selectedPhrase,
  }) {
    return ActionMappingState(
      mappings: mappings ?? this.mappings,
      selectedActor: selectedActor ?? this.selectedActor,
      selectedAction: selectedAction ?? this.selectedAction,
      selectedPhrase: selectedPhrase ?? this.selectedPhrase,
    );
  }
}

class ActionMappingCubit extends Cubit<ActionMappingState> {
  final ActionMappingRepository repo = ActionMappingRepository();
  final RabbitMQProducer producer = RabbitMQProducer(
    exchangeName: "action_mappings",
    routingKey: "action_mapping_service",
  );

  ActionMappingCubit()
    : super(
        ActionMappingState(
          mappings: {},
          selectedActor: null,
          selectedAction: null,
          selectedPhrase: null,
        ),
      ) {
    _init();
  }

  Future<void> _init() async {
    producer.init();
    final data = await repo.read();
    emit(
      ActionMappingState(
        mappings: data,
        selectedActor: data.keys.first,
        selectedAction: data.values.first.keys.first,
        selectedPhrase: data.values.first.values.first.first,
      ),
    );
  }

  void _update(ActionMappingState newState) {
    emit(newState);
    repo.write(newState.mappings);
  }

  void selectActor(Actor actor) {
    final selectedAction = state.mappings[actor]!.keys.first;
    final selectedPhrase = state.mappings[actor]![selectedAction]!.first;

    emit(
      state.copyWith(
        selectedActor: actor,
        selectedAction: selectedAction,
        selectedPhrase: selectedPhrase,
      ),
    );
  }

  void selectAction(Action action) {
    emit(state.copyWith(selectedAction: action, selectedPhrase: null));
  }

  void selectPhrase(Phrase phrase) {
    emit(state.copyWith(selectedPhrase: phrase));
  }

  void addPhrase(Actor actor, Action action, Phrase newPhrase) {
    final updated = ActionMapping.from(state.mappings);
    final actorMap = updated[actor] ?? ActionPhraseMap();
    final phrases = List<Phrase>.from(actorMap[action] ?? []);
    phrases.add(newPhrase);
    actorMap[action] = phrases;
    updated[actor] = actorMap;

    _update(state.copyWith(mappings: updated));
  }

  void updatePhrase(Actor actor, Action action, int index, Phrase newPhrase) {
    final updated = ActionMapping.from(state.mappings);
    final actorMap = updated[actor];
    if (actorMap == null) return;

    final phrases = List<Phrase>.from(actorMap[action] ?? []);
    if (index >= 0 && index < phrases.length) {
      phrases[index] = newPhrase;
      actorMap[action] = phrases;
      updated[actor] = actorMap;
      _update(state.copyWith(mappings: updated));
    }
  }

  void removePhrase(Actor actor, Action action, int index) {
    final updated = ActionMapping.from(state.mappings);
    final actorMap = updated[actor];
    if (actorMap == null) return;

    final phrases = List<Phrase>.from(actorMap[action] ?? []);
    if (index >= 0 && index < phrases.length) {
      phrases.removeAt(index);
      actorMap[action] = phrases;
      updated[actor] = actorMap;
      _update(state.copyWith(mappings: updated));
    }
  }

  void publishMappings() {
    Map<String, dynamic> message = repo.toDomain(state.mappings);
    producer.publish(message);
  }
}
