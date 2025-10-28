import asyncio
import logging
import uuid

from datetime import datetime

from pika.exchange_type import ExchangeType

from cgt_ai_core.log_config import LOG_FORMAT
from cgt_ai_core.rmq_producer import RmqProducer
from cgt_ai_core.service import Service
from cgt_ai_core.service_arg_parser import get_service_arg_parser
from cgt_ai_core.service_runner import run_service

from messages import Foo,Bar


LOGGER = logging.getLogger(__name__)


class TestProducer(Service):
    def __init__(self,
                 host: str = None,
                 port: int = None,
                 username: str = None,
                 password: str = None):
        super().__init__(host, port, username, password)

        self.foo_producer = None
        self.bar_producer = None
        self.add_producer(RmqProducer(connection_params=self.connection_params, exchange_name='foo', exchange_type=ExchangeType.direct, on_producer_ready_callback=self.on_foo_producer_ready))
        self.add_producer(RmqProducer(connection_params=self.connection_params, exchange_name='bar', exchange_type=ExchangeType.direct, on_producer_ready_callback=self.on_bar_producer_ready))

    def on_foo_producer_ready(self, producer: RmqProducer):
        self.foo_producer = producer
        asyncio.create_task(self.publish_foo_message())

    def on_bar_producer_ready(self, producer: RmqProducer):
        self.bar_producer = producer
        asyncio.create_task(self.publish_bar_message())

    async def publish_foo_message(self):
        while True:
            message = Foo(id=uuid.uuid4(), datetime=datetime.now())
            LOGGER.info('Sending foo message on queue %s through routing key %s from exchange %s: %s',
                        self.foo_producer.queue_name, self.foo_producer.routing_key, self.foo_producer.exchange_name, message)
            self.foo_producer.publish_message(message)
            await asyncio.sleep(1)

    async def publish_bar_message(self):
        while True:
            message = Bar(id=uuid.uuid4(), datetime=datetime.now())
            LOGGER.info('Sending bar message on queue %s through routing key %s from exchange %s: %s',
                        self.bar_producer.queue_name, self.bar_producer.routing_key, self.bar_producer.exchange_name, message)
            self.bar_producer.publish_message(message)
            await asyncio.sleep(1)


async def main():
    parser = get_service_arg_parser(description='Test Producer')
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level), format=LOG_FORMAT)
    service = TestProducer(host=args.rmq_host, port=args.rmq_port, username=args.rmq_username, password=args.rmq_password)
    await run_service(service)

if __name__ == '__main__':
    asyncio.run(main())
