import 'package:dart_amqp/dart_amqp.dart';

class RabbitMQProducer {
  final String exchangeName;
  final String routingKey;
  late final Client _client;
  late final Channel _channel;
  late final Exchange _exchange;

  RabbitMQProducer({
    required this.exchangeName,
    required this.routingKey,
    String host = 'localhost',
    int port = 5672,
    String username = 'ai',
    String password = '1q2w3e4r!Q@W#E\$R',
  }) {
    _client = Client(
      settings: ConnectionSettings(
        host: host,
        port: port,
        authProvider: PlainAuthenticator(username, password),
      ),
    );
  }

  Future<void> init() async {
    _channel = await _client.channel();
    _exchange = await _channel.exchange(
      exchangeName,
      ExchangeType.FANOUT,
      durable: false,
    );
  }

  Future<void> publish(Map<String, dynamic> message) async {
    _exchange.publish(message, routingKey);
  }

  Future<void> close() async {
    await _client.close();
  }
}
