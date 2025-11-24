import 'dart:convert';

import 'package:app/messaging/rabbitmq_consumer.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

enum NotificationIcon { bell, check_mark }

Map<NotificationIcon, IconData> notificationIcons = {
  NotificationIcon.bell: Icons.notifications_rounded,
  NotificationIcon.check_mark: Icons.check_circle_outline_rounded,
};

enum NotificationColor { normal, green, red }

Map<NotificationColor, Color> notificationColors = {
  NotificationColor.normal: Color(0xFF2B2B2B),
  NotificationColor.green: Colors.green.shade600,
  NotificationColor.red: Colors.red.shade600,
};

class NotificationMessage {
  final IconData icon;
  final String? title;
  final String? message;
  final Color color;

  NotificationMessage({
    this.icon = Icons.notifications,
    this.title,
    this.message,
    this.color = const Color(0xFF2B2B2B),
  });

  static NotificationMessage fromJson(Map<String, dynamic> json) {
    return NotificationMessage(
      icon: _parseIcon(json['icon'] as int?),
      title: json['title'] as String?,
      message: json['message'] as String?,
      color: _parseColor(json['color'] as int?),
    );
  }

  static IconData _parseIcon(int? value) {
    if (value == null) return _parseIcon(0);
    return notificationIcons[NotificationIcon.values[value]]!;
  }

  static Color _parseColor(int? value) {
    if (value == null) return _parseColor(0);
    return notificationColors[NotificationColor.values[value]]!;
  }
}

class NotificationCubit extends Cubit<NotificationMessage> {
  late final RabbitMQConsumer _consumer;

  NotificationCubit() : super(NotificationMessage()) {
    _consumer = RabbitMQConsumer(
      exchangeName: "gui_notifications",
      queueName: "",
      routingKey: "",
      onMessage: _handleMessage,
    );

    _init();
  }

  void _handleMessage(String message) {
    emit(NotificationMessage.fromJson(jsonDecode(message)));
    emit(NotificationMessage());
  }

  Future<void> _init() async {
    await _consumer.init();
  }

  @override
  Future<void> close() async {
    await _consumer.close();
    return super.close();
  }
}
