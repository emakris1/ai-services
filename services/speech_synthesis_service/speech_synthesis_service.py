import asyncio
import logging

from pika.exchange_type import ExchangeType

from cgt_ai_core.log_config import LOG_FORMAT
from cgt_ai_core.messages import TTSRequestMessage, TTSResponseMessage
from cgt_ai_core.rmq_consumer import RmqConsumer
from cgt_ai_core.rmq_producer import RmqProducer
from cgt_ai_core.rmq_service import RmqService
from cgt_ai_core.service_arg_parser import get_service_arg_parser


LOGGER = logging.getLogger(__name__)


class SpeechSynthesisService(RmqService):
    def __init__(self,
                 host: str = None,
                 port: int = None,
                 username: str = None,
                 password: str = None):
        super().__init__(host, port, username, password)

        self.event_loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()

        self.tts_request_queue: asyncio.Queue[TTSRequestMessage] = asyncio.Queue()

        self.tts_request_consumer: RmqConsumer | None = None
        self.add_consumer(
            RmqConsumer(
                message_type=TTSRequestMessage,
                connection_params=self.connection_params,
                exchange_name='tts_request',
                exchange_type=ExchangeType.direct,
                on_consumer_ready_callback=self.on_tts_request_consumer_ready,
                on_message_callback=self.on_tts_request_message
            )
        )

        self.tts_response_producer: RmqProducer | None = None
        self.add_producer(
            RmqProducer(
                connection_params=self.connection_params,
                exchange_name='tts_response',
                exchange_type=ExchangeType.direct,
                on_producer_ready_callback=self.on_tts_response_producer_ready
            )
        )

    def on_tts_request_consumer_ready(self, consumer: RmqConsumer):
        self.tts_request_consumer = consumer

    def on_tts_request_message(self, _unused_consumer: RmqConsumer, message: TTSRequestMessage):
        self.tts_request_queue.put_nowait(message)

    def on_tts_response_producer_ready(self, producer: RmqProducer):
        self.tts_response_producer = producer
        asyncio.create_task(self.process_tts_requests())

    async def process_tts_requests(self):
        async for message in self.tts_request_generator():
            LOGGER.info('Processing TTS request: %s', message)

    async def tts_request_generator(self):
        while True:
            yield await self.tts_request_queue.get()


async def main():
    parser = get_service_arg_parser(description='Speech Synthesis Service')
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level), format=LOG_FORMAT)

    service = SpeechSynthesisService(
        host=args.rmq_host,
        port=args.rmq_port,
        username=args.rmq_username,
        password=args.rmq_password,
    )
    await service.run()

if __name__ == '__main__':
    asyncio.run(main())
