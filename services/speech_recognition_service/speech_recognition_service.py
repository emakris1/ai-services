import asyncio
import logging

from pika.exchange_type import ExchangeType

from cgt_ai_core.log_config import LOG_FORMAT
from cgt_ai_core.messages import AudioCaptureMessage
from cgt_ai_core.rmq_consumer import RmqConsumer
from cgt_ai_core.rmq_producer import RmqProducer
from cgt_ai_core.service import Service
from cgt_ai_core.service_arg_parser import get_service_arg_parser
from cgt_ai_core.service_runner import run_service


LOGGER = logging.getLogger(__name__)


class SpeechRecognitionService(Service):
    def __init__(self,
                 host: str = None,
                 port: int = None,
                 username: str = None,
                 password: str = None):
        super().__init__(host, port, username, password)

        self.event_loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
        self.audio_capture_queue: asyncio.Queue[AudioCaptureMessage] = asyncio.Queue()

        self.audio_capture_consumer: RmqConsumer | None = None
        self.add_consumer(
            RmqConsumer(
                message_type=AudioCaptureMessage,
                connection_params=self.connection_params,
                exchange_name='audio_capture',
                exchange_type=ExchangeType.direct,
                on_consumer_ready_callback=self.on_audio_capture_consumer_ready,
                on_message_callback=self.on_audio_capture_message
            )
        )

        self.speech_recognition_producer: RmqProducer | None = None
        self.add_producer(
            RmqProducer(
                connection_params=self.connection_params,
                exchange_name='speech_recognition',
                exchange_type=ExchangeType.direct,
                on_producer_ready_callback=self.on_speech_recognition_producer_ready
            )
        )

    def on_audio_capture_consumer_ready(self, consumer: RmqConsumer):
        self.audio_capture_consumer = consumer

    def on_audio_capture_message(self, consumer: RmqConsumer, message: AudioCaptureMessage):
        LOGGER.info('Received audio capture message on queue %s through routing key %s from exchange %s',
                    consumer.queue_name, consumer.routing_key, consumer.exchange_name)
        self.event_loop.call_soon_threadsafe(self.audio_capture_queue.put_nowait, message)

    def on_speech_recognition_producer_ready(self, producer: RmqProducer):
        self.speech_recognition_producer = producer
        asyncio.create_task(self.process_audio())

    async def process_audio(self):
        while True:
            message = await self.audio_capture_queue.get()
            LOGGER.info('Processing audio message')
            self.audio_capture_queue.task_done()


async def main():
    parser = get_service_arg_parser(description='Speech Recognition Service')
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level), format=LOG_FORMAT)

    service = SpeechRecognitionService(
        host=args.rmq_host,
        port=args.rmq_port,
        username=args.rmq_username,
        password=args.rmq_password,
    )
    await run_service(service)

if __name__ == '__main__':
    asyncio.run(main())
