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

        return LayoutBuilder(
          builder: (context, constraints) {
            return Padding(
              padding: const EdgeInsets.fromLTRB(32, 16, 32, 16),
              child: SizedBox(
                height: constraints.maxHeight,
                child: Row(
                  children: [
                    // Left column: actions
                    Expanded(
                      flex: 1,
                      child: Container(
                        height: double.infinity,
                        decoration: BoxDecoration(
                          color: background,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: SingleChildScrollView(
                          padding: const EdgeInsets.all(8),
                          child: Column(
                            children: actions.map((action) {
                              final selected = action == selectedAction;
                              return InkWell(
                                borderRadius: BorderRadius.circular(8),
                                onTap: () => context
                                    .read<ActionMappingCubit>()
                                    .selectAction(action),
                                child: Container(
                                  width: double.infinity,
                                  padding: const EdgeInsets.symmetric(
                                    vertical: 12,
                                    horizontal: 16,
                                  ),
                                  decoration: BoxDecoration(
                                    color: selected
                                        ? selectedColor
                                        : Colors.transparent,
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: Text(
                                    action,
                                    style: theme.textTheme.bodyLarge?.copyWith(
                                      color: selected
                                          ? theme.colorScheme.primary
                                          : textColor,
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
                    ),

                    const SizedBox(width: 16),

                    // Right column: editable actions for selected category
                    Expanded(
                      flex: 2,
                      child: Container(
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
                                child: Column(
                                  children: List.generate(phrases.length, (i) {
                                    final textController =
                                        TextEditingController(text: phrases[i]);

                                    return Container(
                                      margin: const EdgeInsets.symmetric(
                                        vertical: 4,
                                      ),
                                      decoration: BoxDecoration(
                                        color: selectedColor.withOpacity(0.3),
                                        borderRadius: BorderRadius.circular(8),
                                      ),
                                      child: Padding(
                                        padding: const EdgeInsets.symmetric(
                                          horizontal: 12,
                                        ),
                                        child: Row(
                                          children: [
                                            const Icon(
                                              Icons.format_quote_rounded,
                                              size: 16,
                                            ),
                                            Expanded(
                                              child: Padding(
                                                padding:
                                                    const EdgeInsets.symmetric(
                                                      horizontal: 12,
                                                    ),
                                                child: TextField(
                                                  controller: textController,
                                                  onSubmitted: (newValue) =>
                                                      context
                                                          .read<
                                                            ActionMappingCubit
                                                          >()
                                                          .updatePhrase(
                                                            selectedActor!,
                                                            selectedAction!,
                                                            i,
                                                            newValue,
                                                          ),
                                                  decoration:
                                                      const InputDecoration(
                                                        border:
                                                            InputBorder.none,
                                                      ),
                                                ),
                                              ),
                                            ),
                                            IconButton(
                                              icon: const Icon(
                                                Icons.close_rounded,
                                                size: 20,
                                              ),
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
                            Padding(
                              padding: const EdgeInsets.all(12.0),
                              child: Row(
                                mainAxisAlignment: MainAxisAlignment.end,
                                children: [
                                  FilledButton.icon(
                                    icon: const Icon(Icons.add),
                                    label: const Text("Add Phrase"),
                                    onPressed: () => context
                                        .read<ActionMappingCubit>()
                                        .addPhrase(
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
                      ),
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }
}
