import 'package:flutter/material.dart';
import 'package:another_flushbar/flushbar.dart';

class NotificationBar {
  static void show(
    BuildContext context, {
    required String title,
    required String message,
    Color color = Colors.blueGrey,
    IconData icon = Icons.notifications,
    Duration duration = const Duration(seconds: 3),
  }) {
    Flushbar(
      titleText: Text(
        title,
        style: TextStyle(
          fontSize: 15,
          fontWeight: FontWeight.w600,
          color: Colors.white,
        ),
      ),
      messageText: Text(
        message,
        style: TextStyle(fontSize: 14, color: Colors.white70),
      ),
      icon: Icon(icon, size: 26, color: Colors.white),
      duration: duration,
      backgroundColor: color,
      margin: EdgeInsets.fromLTRB(16, 0, 16, 16),
      borderRadius: BorderRadius.circular(10),
      flushbarPosition: FlushbarPosition.BOTTOM,
      flushbarStyle: FlushbarStyle.FLOATING,
      barBlur: 5,
      padding: EdgeInsets.all(14),
    ).show(context);
  }
}
