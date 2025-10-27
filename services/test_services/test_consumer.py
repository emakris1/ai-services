import asyncio
import logging

from pika import ConnectionParameters
from pika.exchange_type import ExchangeType

from cgt_ai_core.log_config import LOG_FORMAT
from cgt_ai_core.rmq_consumer import RmqConsumer
from cgt_ai_core.service import Service
from cgt_ai_core.service_arg_parser import get_service_arg_parser
from cgt_ai_core.service_runner import run_service

from messages import Foo,Bar

LOGGER = logging.getLogger(__name__)


class TestConsumer(Service):
    def __init__(self,
                 connection_params: ConnectionParameters = None,
                 host: str = None,
                 port: int = None,
                 username: str = None,
                 password: str = None):
        super().__init__(connection_params, host, port, username, password)

        self.foo_consumer = None
        self.bar_consumer = None
        self.add_consumer(RmqConsumer(connection_params=self.connection_params, exchange_name='foo', exchange_type=ExchangeType.direct, on_consumer_ready_callback=self.on_foo_consumer_ready, on_message_callback=self.on_foo_message))
        self.add_consumer(RmqConsumer(connection_params=self.connection_params, exchange_name='bar', exchange_type=ExchangeType.direct, on_consumer_ready_callback=self.on_bar_consumer_ready, on_message_callback=self.on_bar_message))

    def on_foo_consumer_ready(self, consumer: RmqConsumer):
        self.foo_consumer = consumer

    def on_bar_consumer_ready(self, consumer: RmqConsumer):
        self.bar_consumer = consumer

    @staticmethod
    def on_foo_message(exchange_name: str, queue_name: str, routing_key: str, body: Foo):
        LOGGER.info('Received foo message on queue %s through routing key %s from exchange %s: %s',
                    queue_name, routing_key, exchange_name, body)

    @staticmethod
    def on_bar_message(exchange_name: str, queue_name: str, routing_key: str, body: Bar):
        LOGGER.info('Received bar message on queue %s through routing key %s from exchange %s: %s',
                    queue_name, routing_key, exchange_name, body)


async def main():
    parser = get_service_arg_parser(description='Test Consumer')
    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level), format=LOG_FORMAT)
    service = TestConsumer(host=args.rmq_host, port=args.rmq_port, username=args.rmq_username, password=args.rmq_password)
    await run_service(service)

if __name__ == '__main__':
    asyncio.run(main())
