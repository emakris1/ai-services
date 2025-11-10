import 'package:app/components/navigation_sidebar.dart';
import 'package:app/cubits/actor_commands_cubit.dart';
import 'package:app/data/actor_commands.dart';
import 'package:app/pages/actor_commands_page.dart';
import 'package:app/theme/themes.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

void main() {
  runApp(
    MultiBlocProvider(
      providers: [BlocProvider(create: (_) => ActorCommandsCubit())],
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
          title: BlocBuilder<ActorCommandsCubit, ActorCommandsState>(
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
              onPressed: () {
                final cubit = context.read<ActorCommandsCubit>();
                cubit.publishMappings();
              },
              iconSize: 26,
            ),
            const SizedBox(width: 12),
          ],
        ),
        drawer: Drawer(child: NavigationSidebar()),
        body: ActorCommandsPage(),
      ),
    );
  }
}
