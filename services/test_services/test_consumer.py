import asyncio
import logging

from pika.exchange_type import ExchangeType

from ai_common.log_config import LOG_FORMAT
from ai_common.service_arg_parser import get_service_arg_parser
from ai_rmq.consumer import RmqConsumer
from ai_rmq.service import RmqService

from test_messages import FooMessage, BarMessage

LOGGER = logging.getLogger(__name__)


class TestConsumer(RmqService):
    def __init__(self,
                 host: str = None,
                 port: int = None,
                 username: str = None,
                 password: str = None,
                 routing_key: str = ''):
        super().__init__(host, port, username, password)

        self.routing_key: str = routing_key

        self.foo_consumer: RmqConsumer | None = None
        self.bar_consumer: RmqConsumer | None = None

        self.add_consumer(
            message_type=FooMessage,
            exchange_name='foo',
            routing_key=self.routing_key,
            exchange_type=ExchangeType.direct,
            on_consumer_ready_callback=self.on_foo_consumer_ready,
            on_message_callback=self.on_foo_message
        )
        self.add_consumer(
            message_type=BarMessage,
            exchange_name='bar',
            routing_key=self.routing_key,
            exchange_type=ExchangeType.direct,
            on_consumer_ready_callback=self.on_bar_consumer_ready,
            on_message_callback=self.on_bar_message
        )

    def on_foo_consumer_ready(self, consumer: RmqConsumer):
        self.foo_consumer = consumer

    def on_bar_consumer_ready(self, consumer: RmqConsumer):
        self.bar_consumer = consumer

    @staticmethod
    def on_foo_message(consumer: RmqConsumer, message: FooMessage):
        LOGGER.info('Received foo message on queue "%s" through routing key "%s" from exchange "%s": %s',
                    consumer.queue_name, consumer.routing_key, consumer.exchange_name, message)

    @staticmethod
    def on_bar_message(consumer: RmqConsumer, message: BarMessage):
        LOGGER.info('Received bar message on queue "%s" through routing key "%s" from exchange "%s": %s',
                    consumer.queue_name, consumer.routing_key, consumer.exchange_name, message)


async def main():
    parser = get_service_arg_parser(description='Test Consumer')
    parser.add_argument_group('Subscription Arguments')
    parser.add_argument('-r', '--routing-key', default='',
                        help='Routing key to subscribe to messages with')
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level), format=LOG_FORMAT)
    service = TestConsumer(
        routing_key=args.routing_key,
        host=args.rmq_host,
        port=args.rmq_port,
        username=args.rmq_username,
        password=args.rmq_password
    )
    await service.run()

if __name__ == '__main__':
    asyncio.run(main())
