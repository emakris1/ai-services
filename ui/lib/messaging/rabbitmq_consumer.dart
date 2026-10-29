import 'package:dart_amqp/dart_amqp.dart';

class RabbitMQConsumer {
  final String exchangeName;
  final String queueName;
  final String routingKey;
  final void Function(String msg) onMessage;

  late final Client _client;
  late final Channel _channel;
  late final Exchange _exchange;
  late final Queue _queue;

  RabbitMQConsumer({
    required this.exchangeName,
    required this.queueName,
    required this.routingKey,
    required this.onMessage,
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

    _exchange = await _channel.exchange(exchangeName, ExchangeType.FANOUT);
    _queue = await _channel.queue(queueName);
    await _queue.bind(_exchange, routingKey);

    final stream = await _queue.consume();
    stream.listen((msg) => onMessage(msg.payloadAsString));
  }

  Future<void> close() => _client.close();
}
