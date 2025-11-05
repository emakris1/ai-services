import 'package:app/components/navigation_sidebar.dart';
import 'package:app/cubits/navigation_cubit.dart';
import 'package:app/pages/driver_action_mapping.dart';
import 'package:app/pages/gunner_action_mapping.dart';
import 'package:app/theme/themes.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

void main() {
  runApp(
    BlocProvider(create: (_) => NavigationCubit(), child: const MainApp()),
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
          title: BlocBuilder<NavigationCubit, AppPage>(
            builder: (context, state) {
              switch (state) {
                case AppPage.driver:
                  return Text("Driver");
                case AppPage.gunner:
                  return Text("Gunner");
              }
            },
          ),
          actions: [
            IconButton(icon: const Icon(Icons.play_arrow), onPressed: () {}),
          ],
        ),
        drawer: Drawer(child: NavigationSidebar()),
        body: BlocBuilder<NavigationCubit, AppPage>(
          builder: (context, state) {
            switch (state) {
              case AppPage.driver:
                return DriverActionMapping();
              case AppPage.gunner:
                return GunnerActionMapping();
            }
          },
        ),
      ),
    );
  }
}
