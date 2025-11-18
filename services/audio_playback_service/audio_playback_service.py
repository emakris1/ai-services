import asyncio
import logging
import sounddevice as sd

from pika.exchange_type import ExchangeType

from cgt_ai_core.log_config import LOG_FORMAT
from cgt_ai_core.messages import TTSResponseMessage
from cgt_ai_core.rmq_consumer import RmqConsumer
from cgt_ai_core.rmq_service import RmqService
from cgt_ai_core.service_arg_parser import get_service_arg_parser


LOGGER = logging.getLogger(__name__)


class AudioPlaybackService(RmqService):
    def __init__(self,
                 host: str = None,
                 port: int = None,
                 username: str = None,
                 password: str = None,
                 device_index: int = None):
        super().__init__(host, port, username, password)

        if device_index is not None:
            self.device: dict = sd.query_devices(device_index)
        else:
            LOGGER.info('No audio device index provided. Playing on default output audio device.')
            self.device: dict = sd.query_devices(kind='output')
        self.device_index: int = self.device['index']
        self.device_name: str = self.device['name']

        LOGGER.info('Playing on audio device {index: %d, name: %s}.', self.device_index, self.device_name)

        self.tts_response_queue: asyncio.Queue[TTSResponseMessage] = asyncio.Queue()

        self.tts_response_consumer: RmqConsumer | None = None
        self.add_consumer(
            RmqConsumer(
                message_type=TTSResponseMessage,
                connection_params=self.connection_params,
                exchange_name='tts_response',
                exchange_type=ExchangeType.direct,
                on_consumer_ready_callback=self.on_tts_response_consumer_ready,
                on_message_callback=self.on_tts_response_message
            )
        )

    def on_tts_response_consumer_ready(self, consumer: RmqConsumer):
        self.tts_response_consumer = consumer
        asyncio.create_task(self.process_tts_responses())

    def on_tts_response_message(self, _unused_consumer: RmqConsumer, message: TTSResponseMessage):
        self.tts_response_queue.put_nowait(message)

    async def process_tts_responses(self):
        async for message in self.tts_response_generator():
            LOGGER.info('Processing TTS response')

    async def tts_response_generator(self):
        while True:
            yield await self.tts_response_queue.get()


async def main():
    parser = get_service_arg_parser(description='Audio Playback Service')
    device_group = parser.add_argument_group('Device Arguments')
    device_group.add_argument('-x', '--device-index', type=int, default=None,
                              help='Index of audio device to play on')
    device_group.add_argument('-m', '--device-prompt', action='store_true',
                              help='Show a prompt to select which audio device to play on from a list of available devices')
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level), format=LOG_FORMAT)

    if args.device_index is None:
        # index and prompt are mutually exclusive - only show prompt if an index is not provided
        if args.device_prompt:
            print(sd.query_devices())
            input_str = input('Enter index of audio device to play on (or press Enter for default): ').strip()
            try:
                args.device_index = int(input_str) if input_str else None
            except ValueError as exc:
                LOGGER.exception('Invalid audio device index provided.', exc_info=exc)
                args.device_index = None

    service = AudioPlaybackService(
        host=args.rmq_host,
        port=args.rmq_port,
        username=args.rmq_username,
        password=args.rmq_password,
        device_index=args.device_index,
    )
    await service.run()

if __name__ == '__main__':
    asyncio.run(main())
