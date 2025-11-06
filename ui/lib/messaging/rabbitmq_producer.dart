import "package:app/messaging/rabbitmq_connection.dart";
import "package:dart_amqp/dart_amqp.dart";

class RabbitMQProducer {
  late final RabbitMQConnection connection;
  final String queueName;
  late final Queue _queue;

  RabbitMQProducer({required this.connection, required this.queueName}) {
    _init();
  }

  Future<void> _init() async {
    _queue = await connection.openQueue(queueName);
  }

  void publish(Map<String, dynamic> message) {
    _queue.publish(message);
  }
}
