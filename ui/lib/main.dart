import 'package:app/components/navigation_sidebar.dart';
import 'package:app/components/notification_bar.dart';
import 'package:app/cubits/actor_commands_cubit.dart';
import 'package:app/cubits/notification_cubit.dart';
import 'package:app/data/actor_commands.dart';
import 'package:app/pages/actor_commands_page.dart';
import 'package:app/theme/themes.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

void main() {
  runApp(
    MultiBlocProvider(
      providers: [
        BlocProvider(create: (_) => ActorCommandsCubit()),
        BlocProvider(create: (_) => NotificationCubit()),
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
      home: BlocListener<NotificationCubit, NotificationMessage>(
        listenWhen: (p, c) => c.message != null,
        listener: (context, state) async {
          NotificationBar.show(
            context,
            icon: state.icon,
            title: state.title ?? "",
            message: state.message ?? "",
            color: state.color,
          );
        },
        child: RootScaffold(),
      ),
    );
  }
}

class RootScaffold extends StatelessWidget {
  const RootScaffold({super.key});

  @override
  Widget build(BuildContext context) {
    return Builder(
      builder: (rootContext) => Scaffold(
        appBar: AppBar(
          title: const ActorTitle(),
          actions: [
            SaveMappingsButton(rootContext: rootContext),
            const SizedBox(width: 12),
          ],
        ),
        drawer: const Drawer(child: NavigationSidebar()),
        body: const ActorCommandsPage(),
      ),
    );
  }
}

class ActorTitle extends StatelessWidget {
  const ActorTitle({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<ActorCommandsCubit, ActorCommandsState>(
      builder: (context, state) {
        switch (state.selectedActor) {
          case Actor.driver:
            return const Text("Driver");
          case Actor.gunner:
            return const Text("Gunner");
          default:
            return const Text("Unknown");
        }
      },
    );
  }
}

class SaveMappingsButton extends StatelessWidget {
  final BuildContext rootContext;

  const SaveMappingsButton({super.key, required this.rootContext});

  @override
  Widget build(BuildContext context) {
    return IconButton(
      icon: const Icon(Icons.play_arrow_rounded),
      iconSize: 26,
      onPressed: () async {
        rootContext.read<ActorCommandsCubit>().publishMappings();
      },
    );
  }
}
