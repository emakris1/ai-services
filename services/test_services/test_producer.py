import asyncio
import logging

from pika import ConnectionParameters
from pika.exchange_type import ExchangeType

from cgt_ai_core.log_config import LOG_FORMAT
from cgt_ai_core.rmq_producer import RmqProducer
from cgt_ai_core.service import Service
from cgt_ai_core.service_arg_parser import get_service_arg_parser


LOGGER = logging.getLogger(__name__)


class TestProducer(Service):
    def __init__(self,
                 connection_params: ConnectionParameters = None,
                 host: str = None,
                 port: int = None,
                 username: str = None,
                 password: str = None):
        super().__init__(connection_params, host, port, username, password)

        self.add_producer(RmqProducer(on_producer_ready_callback=self.on_foo_producer_ready, connection_params=self.connection_params, exchange_name='foo', exchange_type=ExchangeType.direct))
        self.add_producer(RmqProducer(on_producer_ready_callback=self.on_bar_producer_ready, connection_params=self.connection_params, exchange_name='bar', exchange_type=ExchangeType.direct))

    @staticmethod
    def on_foo_producer_ready(producer: RmqProducer):
        producer.publish_message(message='foo')

    @staticmethod
    def on_bar_producer_ready(producer: RmqProducer):
        producer.publish_message(message='bar')


async def main():
    parser = get_service_arg_parser(description='Test Producer')
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level), format=LOG_FORMAT)

    service = TestProducer(host=args.rmq_host, port=args.rmq_port, username=args.rmq_username, password=args.rmq_password)
    await service.run()

if __name__ == '__main__':
    asyncio.run(main())
