import 'dart:convert';
import "package:app/messaging/rabbitmq_connection.dart";
import "package:dart_amqp/dart_amqp.dart";

class RabbitMQConsumer {
  late final RabbitMQConnection connection;
  late final Queue _queue;
  final Function(Map<String, dynamic>) callback;

  RabbitMQConsumer({required this.connection, required this.callback}) {
    _init();
  }

  Future<void> _init() async {
    _queue = await connection.openQueue("hello");
  }

  Future<void> start() async {
    Consumer consumer = await _queue.consume();
    consumer.listen(_callback);
  }

  void _callback(AmqpMessage message) {
    try {
      final json = jsonDecode(message.payloadAsString) as Map<String, dynamic>;
      callback(json);
      message.ack();
    } catch (e) {
      message.reject(false);
    }
  }
}
