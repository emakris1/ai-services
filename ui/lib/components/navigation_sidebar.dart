import 'package:app/cubits/action_mapping_cubit.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

class NavigationSidebar extends StatelessWidget {
  const NavigationSidebar({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<ActionMappingCubit, ActionMappingState>(
      builder: (context, state) {
        return ListView(
          padding: EdgeInsets.zero,
          children: [
            SizedBox(
              height: 60,
              child: DrawerHeader(
                margin: EdgeInsets.zero,
                padding: EdgeInsets.all(16),
                child: Text('Select Actor', style: TextStyle(fontSize: 20)),
              ),
            ),
            NavigationTile(
              title: 'Driver',
              icon: Icons.directions_car_rounded,
              actor: Actor.driver,
              isSelected: state.selectedActor == Actor.driver,
            ),
            NavigationTile(
              title: 'Gunner',
              icon: Icons.person_rounded,
              actor: Actor.gunner,
              isSelected: state.selectedActor == Actor.gunner,
            ),
          ],
        );
      },
    );
  }
}

class NavigationTile extends StatelessWidget {
  final String title;
  final IconData icon;
  final Actor actor;
  final bool isSelected;

  const NavigationTile({
    super.key,
    required this.title,
    required this.icon,
    required this.actor,
    required this.isSelected,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      selected: isSelected,
      leading: Icon(icon),
      title: Text(title),
      onTap: () {
        Navigator.pop(context);
        context.read<ActionMappingCubit>().selectActor(actor);
      },
    );
  }
}
