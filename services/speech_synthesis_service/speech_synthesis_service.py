import asyncio
import kokoro
import logging

from pika.exchange_type import ExchangeType

import ai_common.enums.tts as tts

from ai_common.log_config import LOG_FORMAT
from ai_common.messages import AudioMessage, TTSRequestMessage
from ai_common.service_arg_parser import get_service_arg_parser
from ai_rmq.consumer import RmqConsumer
from ai_rmq.producer import RmqProducer
from ai_rmq.runner import run_service
from ai_rmq.service import RmqService

LOGGER = logging.getLogger(__name__)


class SpeechSynthesisService(RmqService):
    def __init__(self,
                 host: str = None,
                 port: int = None,
                 username: str = None,
                 password: str = None):
        super().__init__(host, port, username, password)

        self.tts_request_queue: asyncio.Queue[TTSRequestMessage] = asyncio.Queue()
        self.process_tts_requests_task: asyncio.Task | None = None

        self.channels: int = 1 # Kokoro only returns mono audio
        self.sample_rate: int = 24000 # Kokoro only returns 24kHz audio

        self.tts_request_consumer: RmqConsumer | None = None
        self.add_consumer(
            message_type=TTSRequestMessage,
            exchange_name='tts_request',
            exchange_type=ExchangeType.direct,
            on_consumer_ready_callback=self.on_tts_request_consumer_ready,
            on_message_callback=self.on_tts_request_message
        )

        self.audio_playback_producer: RmqProducer | None = None
        self.add_producer(
            exchange_name='audio_playback',
            exchange_type=ExchangeType.direct,
            on_producer_ready_callback=self.on_audio_playback_producer_ready
        )

        self.model: kokoro.KModel = kokoro.KModel()
        self.pipelines: dict[tts.Language, kokoro.KPipeline] = {}
        for language in tts.Language:
            self.pipelines[language]: kokoro.KPipeline = kokoro.KPipeline(
                lang_code=language.value,
                model=self.model,
                device='cuda'
            )

    def on_tts_request_consumer_ready(self, consumer: RmqConsumer):
        self.tts_request_consumer = consumer

    def on_tts_request_message(self, _unused_consumer: RmqConsumer, message: TTSRequestMessage):
        try:
            self.tts_request_queue.put_nowait(message)
        except asyncio.QueueFull:
            LOGGER.warning('TTS request queue is full. Discarding TTS request message.')
        except asyncio.QueueShutDown:
            LOGGER.warning('TTS request queue is shut down. Discarding TTS request message.')

    def on_audio_playback_producer_ready(self, producer: RmqProducer):
        self.audio_playback_producer = producer

    def on_service_ready(self):
        super().on_service_ready()
        self.process_tts_requests_task = asyncio.create_task(self.process_tts_requests())

    async def process_tts_requests(self):
        async for tts_req_msg in self.tts_request_generator():
            LOGGER.info('Processing TTS request: %s', tts_req_msg)

            if tts_req_msg.language not in self.pipelines:
                LOGGER.warning(
                    'No pipeline found for language %s. Discarding request.',
                    tts_req_msg.language
                )
                continue

            generator = self.pipelines[tts_req_msg.language](text=tts_req_msg.text, voice=tts_req_msg.voice.value)
            for graphemes, phonemes, speech_tensor in generator:
                audio_msg = AudioMessage(
                    sample_rate=self.sample_rate,
                    samples=speech_tensor.detach().cpu().numpy()
                )
                LOGGER.info('Publishing audio playback message.')
                self.audio_playback_producer.publish_message(audio_msg)

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
    run_service(main())
