import "package:dart_amqp/dart_amqp.dart";

class RabbitMQConnection {
  late final Client _client;

  RabbitMQConnection() {
    final settings = ConnectionSettings(
      host: 'localhost',
      port: 5672,
      authProvider: const PlainAuthenticator('guest', 'guest'),
    );

    _client = Client(settings: settings);
  }

  Client getClient() {
    return _client;
  }

  Future<Queue> openQueue(String queueName) async {
    final channel = await _client.channel();
    return await channel.queue(queueName, durable: true);
  }
}
