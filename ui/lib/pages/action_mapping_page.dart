import 'package:app/cubits/action_mapping_cubit.dart';
import 'package:flutter/material.dart' hide Action;
import 'package:flutter_bloc/flutter_bloc.dart';

class ActionMappingPage extends StatelessWidget {
  const ActionMappingPage({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final background = theme.colorScheme.surfaceVariant.withOpacity(0.3);
    final selectedColor = theme.colorScheme.primary.withOpacity(0.15);
    final textColor = theme.colorScheme.onSurface;

    return BlocBuilder<ActionMappingCubit, ActionMappingState>(
      builder: (context, state) {
        final selectedAction = state.selectedAction;
        final selectedActor = state.selectedActor;

        Iterable<Action> actions = [];
        List<Phrase> phrases = [];

        if (selectedAction != null && selectedActor != null) {
          final actorActionMappings = state.mappings[selectedActor]!;
          actions = actorActionMappings.keys;
          phrases = actorActionMappings[selectedAction]!;
        }

        return Padding(
          padding: const EdgeInsets.fromLTRB(32, 16, 32, 16),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Expanded(
                flex: 1,
                child: ActionsList(
                  actions: actions,
                  selectedAction: selectedAction,
                  background: background,
                  selectedColor: selectedColor,
                  textColor: textColor,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                flex: 2,
                child: RightPanel(
                  phrases: phrases,
                  selectedActor: selectedActor,
                  selectedAction: selectedAction,
                  background: background,
                  selectedColor: selectedColor,
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class ActionsList extends StatelessWidget {
  final Iterable<Action> actions;
  final Action? selectedAction;
  final Color background;
  final Color selectedColor;
  final Color textColor;

  const ActionsList({
    super.key,
    required this.actions,
    required this.selectedAction,
    required this.background,
    required this.selectedColor,
    required this.textColor,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      height: double.infinity,
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(12),
      ),
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(8),
        child: Align(
          alignment: Alignment.topCenter,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: actions.map((action) {
              final selected = action == selectedAction;
              return InkWell(
                borderRadius: BorderRadius.circular(8),
                onTap: () =>
                    context.read<ActionMappingCubit>().selectAction(action),
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    vertical: 12,
                    horizontal: 16,
                  ),
                  decoration: BoxDecoration(
                    color: selected ? selectedColor : Colors.transparent,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    action,
                    style: theme.textTheme.bodyLarge?.copyWith(
                      color: selected ? theme.colorScheme.primary : textColor,
                      fontWeight: selected
                          ? FontWeight.w500
                          : FontWeight.normal,
                    ),
                  ),
                ),
              );
            }).toList(),
          ),
        ),
      ),
    );
  }
}

class RightPanel extends StatelessWidget {
  final List<Phrase> phrases;
  final Actor? selectedActor;
  final Action? selectedAction;
  final Color background;
  final Color selectedColor;

  const RightPanel({
    super.key,
    required this.phrases,
    required this.selectedActor,
    required this.selectedAction,
    required this.background,
    required this.selectedColor,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        ResponseInput(background: background, selectedColor: selectedColor),
        Expanded(
          child: PhrasesList(
            phrases: phrases,
            selectedActor: selectedActor,
            selectedAction: selectedAction,
            background: background,
            selectedColor: selectedColor,
          ),
        ),
      ],
    );
  }
}

class ResponseInput extends StatelessWidget {
  final Color background;
  final Color selectedColor;

  const ResponseInput({
    super.key,
    required this.background,
    required this.selectedColor,
  });

  @override
  Widget build(BuildContext context) {
    final controller = TextEditingController(text: "New Response");

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(12),
      ),
      padding: const EdgeInsets.all(8),
      child: Container(
        decoration: BoxDecoration(
          color: selectedColor.withOpacity(0.3),
          borderRadius: BorderRadius.circular(8),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 12),
        child: Row(
          children: [
            const Icon(Icons.spatial_audio_off_rounded, size: 18),
            Expanded(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                child: TextField(
                  controller: controller,
                  decoration: const InputDecoration(
                    border: InputBorder.none,
                    hintText: "Response",
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class PhrasesList extends StatelessWidget {
  final List<Phrase> phrases;
  final Actor? selectedActor;
  final Action? selectedAction;
  final Color background;
  final Color selectedColor;

  const PhrasesList({
    super.key,
    required this.phrases,
    required this.selectedActor,
    required this.selectedAction,
    required this.background,
    required this.selectedColor,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: double.infinity,
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: [
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(8),
              child: Align(
                alignment: Alignment.topLeft,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: List.generate(phrases.length, (i) {
                    final controller = TextEditingController(text: phrases[i]);
                    return Container(
                      margin: const EdgeInsets.symmetric(vertical: 4),
                      decoration: BoxDecoration(
                        color: selectedColor.withOpacity(0.3),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 12),
                        child: Row(
                          children: [
                            const Icon(Icons.format_quote_rounded, size: 16),
                            Expanded(
                              child: Padding(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 12,
                                ),
                                child: TextField(
                                  controller: controller,
                                  onSubmitted: (value) => context
                                      .read<ActionMappingCubit>()
                                      .updatePhrase(
                                        selectedActor!,
                                        selectedAction!,
                                        i,
                                        value,
                                      ),
                                  decoration: const InputDecoration(
                                    border: InputBorder.none,
                                  ),
                                ),
                              ),
                            ),
                            IconButton(
                              icon: const Icon(Icons.close_rounded, size: 20),
                              onPressed: () => context
                                  .read<ActionMappingCubit>()
                                  .removePhrase(
                                    selectedActor!,
                                    selectedAction!,
                                    i,
                                  ),
                            ),
                          ],
                        ),
                      ),
                    );
                  }),
                ),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                FilledButton.icon(
                  icon: const Icon(Icons.add),
                  label: const Text("Add Phrase"),
                  onPressed: () => context.read<ActionMappingCubit>().addPhrase(
                    selectedActor!,
                    selectedAction!,
                    "New phrase",
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
