import asyncio
import kokoro
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

        self.tts_request_queue: asyncio.Queue[TTSRequestMessage] = asyncio.Queue()

        self.sample_rate = 24000 # Kokoro always returns 24kHz audio

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

        self.pipeline = kokoro.KPipeline(
            lang_code='a',
            device='cuda'
        )

    def on_tts_request_consumer_ready(self, consumer: RmqConsumer):
        self.tts_request_consumer = consumer

    def on_tts_request_message(self, _unused_consumer: RmqConsumer, message: TTSRequestMessage):
        self.tts_request_queue.put_nowait(message)

    def on_tts_response_producer_ready(self, producer: RmqProducer):
        self.tts_response_producer = producer
        asyncio.create_task(self.process_tts_requests())

    async def process_tts_requests(self):
        async for tts_req_msg in self.tts_request_generator():
            LOGGER.info('Processing TTS request: %s', tts_req_msg)
            generator = self.pipeline(tts_req_msg.text, voice=tts_req_msg.voice)
            for i, (graphemes, phonemes, speech_tensor) in enumerate(generator):
                tts_resp_msg = TTSResponseMessage(
                    sample_rate=self.sample_rate,
                    speech=speech_tensor.detach().cpu().numpy().tobytes()
                )
                LOGGER.info('Publishing TTS response message')
                self.tts_response_producer.publish_message(tts_resp_msg)

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
