import 'package:app/cubits/actor_commands_cubit.dart';
import 'package:app/data/actor_commands.dart';
import 'package:flutter/material.dart' hide Action;
import 'package:flutter_bloc/flutter_bloc.dart';

class ActorCommandsPage extends StatelessWidget {
  const ActorCommandsPage({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final background = theme.colorScheme.surfaceVariant.withOpacity(0.3);
    final selectedColor = theme.colorScheme.primary.withOpacity(0.15);
    final textColor = theme.colorScheme.onSurface;

    return BlocBuilder<ActorCommandsCubit, ActorCommandsState>(
      builder: (context, state) {
        final selectedActor = state.selectedActor;
        final selectedAction = state.selectedAction;

        Iterable<Action> actions = [];
        String reply = "";
        String label = "";

        if (selectedActor != null && selectedAction != null) {
          final actorCommands = state.config.commands.firstWhere(
            (a) => a.actor == selectedActor,
          );
          final command = actorCommands.commands.firstWhere(
            (c) => c.action == selectedAction,
          );
          actions = actorCommands.commands.map((c) => c.action);
          label = command.label;
          reply = command.reply;
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
                  label: label,
                  reply: reply,
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
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: actions.map((action) {
            final selected = action == selectedAction;
            return InkWell(
              borderRadius: BorderRadius.circular(8),
              onTap: () =>
                  context.read<ActorCommandsCubit>().selectAction(action),
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
                  action.name
                      .split('_')
                      .map((word) => word[0].toUpperCase() + word.substring(1))
                      .join(' '),
                  style: theme.textTheme.bodyLarge?.copyWith(
                    color: selected ? theme.colorScheme.primary : textColor,
                    fontWeight: selected ? FontWeight.w500 : FontWeight.normal,
                  ),
                ),
              ),
            );
          }).toList(),
        ),
      ),
    );
  }
}

class RightPanel extends StatelessWidget {
  final String label;
  final String reply;
  final Actor? selectedActor;
  final Action? selectedAction;
  final Color background;
  final Color selectedColor;

  const RightPanel({
    super.key,
    required this.label,
    required this.reply,
    required this.selectedActor,
    required this.selectedAction,
    required this.background,
    required this.selectedColor,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        LabelInput(
          label: label,
          actor: selectedActor,
          action: selectedAction,
          background: background,
          selectedColor: selectedColor,
        ),
        ResponseInput(
          reply: reply,
          selectedActor: selectedActor,
          selectedAction: selectedAction,
          background: background,
          selectedColor: selectedColor,
        ),
      ],
    );
  }
}

class ResponseInput extends StatelessWidget {
  final String reply;
  final Actor? selectedActor;
  final Action? selectedAction;
  final Color background;
  final Color selectedColor;

  const ResponseInput({
    super.key,
    required this.reply,
    required this.selectedActor,
    required this.selectedAction,
    required this.background,
    required this.selectedColor,
  });

  @override
  Widget build(BuildContext context) {
    final controller = TextEditingController(text: reply);

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
                  onSubmitted: (value) => context
                      .read<ActorCommandsCubit>()
                      .updateReply(selectedActor!, selectedAction!, value),
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

class LabelInput extends StatelessWidget {
  final String label;
  final Actor? actor;
  final Action? action;
  final Color background;
  final Color selectedColor;

  const LabelInput({
    super.key,
    required this.label,
    required this.actor,
    required this.action,
    required this.background,
    required this.selectedColor,
  });

  @override
  Widget build(BuildContext context) {
    final controller = TextEditingController(text: label);

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
            const Icon(Icons.short_text_rounded, size: 18),
            Expanded(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                child: TextField(
                  controller: controller,
                  onSubmitted: (value) => context
                      .read<ActorCommandsCubit>()
                      .updateLabel(actor!, action!, value),
                  decoration: const InputDecoration(
                    border: InputBorder.none,
                    hintText: "Label",
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
