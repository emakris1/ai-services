import 'package:flutter_bloc/flutter_bloc.dart';

enum Actor { driver, gunner }

typedef Action = String;
typedef Phrase = String;

typedef ActionPhraseMap = Map<Action, List<Phrase>>;

class ActionMappingState {
  final Map<Actor, ActionPhraseMap> mappings;
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
    Map<Actor, ActionPhraseMap>? mappings,
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
  ActionMappingCubit(Map<Actor, ActionPhraseMap> initial)
    : super(
        ActionMappingState(
          mappings: initial,
          selectedActor: initial.keys.first,
          selectedAction: initial.values.first.keys.first,
          selectedPhrase: initial.values.first.values.first.first,
        ),
      );

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
    final updated = Map<Actor, ActionPhraseMap>.from(state.mappings);
    final actorMap = updated[actor] ?? ActionPhraseMap();
    final phrases = List<Phrase>.from(actorMap[action] ?? []);
    phrases.add(newPhrase);
    actorMap[action] = phrases;
    updated[actor] = actorMap;
    emit(state.copyWith(mappings: updated));
  }

  void updatePhrase(Actor actor, Action action, int index, Phrase newPhrase) {
    final updated = Map<Actor, ActionPhraseMap>.from(state.mappings);
    final actorMap = updated[actor];
    if (actorMap == null) return;

    final phrases = List<Phrase>.from(actorMap[action] ?? []);
    if (index >= 0 && index < phrases.length) {
      phrases[index] = newPhrase;
      actorMap[action] = phrases;
      updated[actor] = actorMap;
      emit(state.copyWith(mappings: updated));
    }
  }

  void removePhrase(Actor actor, Action action, int index) {
    final updated = Map<Actor, ActionPhraseMap>.from(state.mappings);
    final actorMap = updated[actor];
    if (actorMap == null) return;

    final phrases = List<Phrase>.from(actorMap[action] ?? []);
    if (index >= 0 && index < phrases.length) {
      phrases.removeAt(index);
      actorMap[action] = phrases;
      updated[actor] = actorMap;
      emit(state.copyWith(mappings: updated));
    }
  }
}
