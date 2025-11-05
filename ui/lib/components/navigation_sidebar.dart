import 'package:app/cubits/navigation_cubit.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

class NavigationSidebar extends StatelessWidget {
  const NavigationSidebar({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<NavigationCubit, AppPage>(
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
              page: AppPage.driver,
              state: state,
            ),
            NavigationTile(
              title: 'Gunner',
              icon: Icons.person_rounded,
              page: AppPage.gunner,
              state: state,
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
  final AppPage page;
  final AppPage state;

  const NavigationTile({
    super.key,
    required this.title,
    required this.icon,
    required this.page,
    required this.state,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      selected: state == page,
      leading: Icon(icon),
      title: Text(title),
      onTap: () {
        Navigator.pop(context);
        context.read<NavigationCubit>().selectPage(page);
      },
    );
  }
}
