import 'package:flutter_bloc/flutter_bloc.dart';

enum AppPage { driver, gunner }

class NavigationCubit extends Cubit<AppPage> {
  NavigationCubit() : super(AppPage.driver);

  void selectPage(AppPage page) => emit(page);
}
