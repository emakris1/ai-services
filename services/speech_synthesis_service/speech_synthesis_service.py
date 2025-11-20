import asyncio
import kokoro
import logging
import numpy as np

from pika.exchange_type import ExchangeType

import cgt_ai_core.tts_enums as tts

from cgt_ai_core.log_config import LOG_FORMAT
from cgt_ai_core.messages import TTSRequestMessage, AudioMessage
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

        self.channels: int = 1 # Kokoro only returns mono audio
        self.sample_rate: int = 24000 # Kokoro only returns 24kHz audio

        self.speech_cache: dict[tuple[tts.Language, tts.Voice, str], list[np.ndarray]] = {}

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

        self.audio_playback_producer: RmqProducer | None = None
        self.add_producer(
            RmqProducer(
                connection_params=self.connection_params,
                exchange_name='audio_playback',
                exchange_type=ExchangeType.direct,
                on_producer_ready_callback=self.on_audio_playback_producer_ready
            )
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
        asyncio.create_task(self.process_tts_requests())

    async def process_tts_requests(self):
        async for tts_req_msg in self.tts_request_generator():
            LOGGER.info('Processing TTS request: %s', tts_req_msg)

            if tts_req_msg.language not in self.pipelines:
                LOGGER.warning(
                    'No pipeline found for language %s. Discarding request.',
                    tts_req_msg.language
                )
                continue

            key = (tts_req_msg.language, tts_req_msg.voice, tts_req_msg.text)
            if key in self.speech_cache:
                speech_chunks = self.speech_cache[key]
            else:
                speech_chunks = []
                generator = self.pipelines[tts_req_msg.language](tts_req_msg.text, voice=tts_req_msg.voice.value)
                for index, (graphemes, phonemes, speech_tensor) in enumerate(generator):
                    speech_chunks.append(speech_tensor.detach().cpu().numpy())
                if tts_req_msg.cache_speech:
                    self.speech_cache[key] = speech_chunks

            if tts_req_msg.play_immediately:
                for speech_chunk in speech_chunks:
                    audio_msg = AudioMessage(
                        sample_rate=self.sample_rate,
                        samples=speech_chunk
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
    asyncio.run(main())
