import asyncio
import logging
import uuid

from datetime import datetime

from pika.exchange_type import ExchangeType

from cgt_ai_core.log_config import LOG_FORMAT
from cgt_ai_core.rmq_producer import RmqProducer
from cgt_ai_core.service import Service
from cgt_ai_core.service_arg_parser import get_service_arg_parser

from test_messages import FooMessage, BarMessage


LOGGER = logging.getLogger(__name__)


class TestProducer(Service):
    def __init__(self,
                 host: str = None,
                 port: int = None,
                 username: str = None,
                 password: str = None,
                 routing_key: str = '',
                 publish_interval: float = 1.0):
        super().__init__(host, port, username, password)

        self.routing_key: str = routing_key
        self.publish_interval: float = publish_interval

        self.foo_producer: RmqProducer | None = None
        self.bar_producer: RmqProducer | None = None
        self.add_producer(
            RmqProducer(
                connection_params=self.connection_params,
                exchange_name='foo',
                routing_key=self.routing_key,
                exchange_type=ExchangeType.direct,
                on_producer_ready_callback=self.on_foo_producer_ready
            )
        )
        self.add_producer(
            RmqProducer(
                connection_params=self.connection_params,
                exchange_name='bar',
                routing_key=self.routing_key,
                exchange_type=ExchangeType.direct,
                on_producer_ready_callback=self.on_bar_producer_ready
            )
        )

    def on_foo_producer_ready(self, producer: RmqProducer):
        self.foo_producer = producer
        asyncio.create_task(self.publish_foo_message())

    def on_bar_producer_ready(self, producer: RmqProducer):
        self.bar_producer = producer
        asyncio.create_task(self.publish_bar_message())

    async def publish_foo_message(self):
        while True:
            message = FooMessage(id=uuid.uuid4(), datetime=datetime.now())
            LOGGER.info('Sending foo message to exchange "%s" with routing key "%s": %s',
                        self.foo_producer.exchange_name, self.foo_producer.routing_key, message
            )
            self.foo_producer.publish_message(message)
            await asyncio.sleep(self.publish_interval)

    async def publish_bar_message(self):
        while True:
            message = BarMessage(id=uuid.uuid4(), datetime=datetime.now())
            LOGGER.info('Sending bar message to exchange "%s" with routing key "%s": %s',
                        self.bar_producer.exchange_name, self.bar_producer.routing_key, message
            )
            self.bar_producer.publish_message(message)
            await asyncio.sleep(self.publish_interval)


async def main():
    parser = get_service_arg_parser(description='Test Producer')
    parser.add_argument_group('Publication Arguments')
    parser.add_argument('-r', '--routing-key', default='',
                        help='Routing key to publish messages with')
    parser.add_argument('-v', '--publish-interval', type=float, default=1.0,
                        help='Interval in seconds between publishing messages')
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level), format=LOG_FORMAT)
    service = TestProducer(
        routing_key=args.routing_key,
        publish_interval=args.publish_interval,
        host=args.rmq_host,
        port=args.rmq_port,
        username=args.rmq_username,
        password=args.rmq_password
    )
    await service.run()

if __name__ == '__main__':
    asyncio.run(main())
