import 'package:app/components/navigation_sidebar.dart';
import 'package:app/cubits/action_mapping_cubit.dart';
import 'package:app/pages/action_mapping_page.dart';
import 'package:app/theme/themes.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

final defaultMappings = {
  Actor.driver: {
    "Accelerate": ["Move forward", "Go ahead", "Step on it", "Drive forward"],
    "Brake": ["Slow down", "Stop", "Ease up", "Hit the brakes"],
    "Turn Left": ["Turn left", "Go left", "Steer left", "Left turn"],
    "Turn Right": ["Turn right", "Go right", "Steer right", "Right turn"],
    "Horn": ["Honk", "Sound the horn", "Beep", "Alert"],
  },
  Actor.gunner: {
    "Aim": [
      "Aim here",
      "Line up the target",
      "Get the target in sight",
      "Focus fire",
    ],
    "Fire": ["Shoot", "Fire!", "Open fire", "Engage target"],
    "Reload": ["Reload weapon", "Prepare ammo", "Load again", "Refill rounds"],
    "Switch Weapon": [
      "Change weapon",
      "Switch guns",
      "Next weapon",
      "Swap armament",
    ],
    "Spot Target": [
      "Mark that target",
      "Spot enemy",
      "Identify target",
      "Tag it",
    ],
  },
};

void main() {
  runApp(
    MultiBlocProvider(
      providers: [
        BlocProvider(create: (_) => ActionMappingCubit(defaultMappings)),
      ],
      child: const MainApp(),
    ),
  );
}

class MainApp extends StatelessWidget {
  const MainApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Dark Mode Demo',
      theme: lightTheme,
      darkTheme: darkTheme,
      themeMode: ThemeMode.system,
      debugShowCheckedModeBanner: false,
      home: Scaffold(
        appBar: AppBar(
          title: BlocBuilder<ActionMappingCubit, ActionMappingState>(
            builder: (context, state) {
              switch (state.selectedActor) {
                case Actor.driver:
                  return Text("Driver");
                case Actor.gunner:
                  return Text("Gunner");
                default:
                  return Text("Unknown");
              }
            },
          ),
          actions: [
            IconButton(
              icon: const Icon(Icons.play_arrow_rounded),
              onPressed: () {},
              iconSize: 26,
            ),
            const SizedBox(width: 12),
          ],
        ),
        drawer: Drawer(child: NavigationSidebar()),
        body: ActionMappingPage(),
      ),
    );
  }
}
