import asyncio
import logging
import sounddevice as sd

from pika.exchange_type import ExchangeType

from cgt_ai_core.log_config import LOG_FORMAT
from cgt_ai_core.messages import AudioMessage
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

        self.audio_playback_queue: asyncio.Queue[AudioMessage] = asyncio.Queue()

        self.audio_playback_consumer: RmqConsumer | None = None
        self.add_consumer(
            RmqConsumer(
                message_type=AudioMessage,
                connection_params=self.connection_params,
                exchange_name='audio_playback',
                exchange_type=ExchangeType.direct,
                on_consumer_ready_callback=self.on_audio_playback_consumer_ready,
                on_message_callback=self.on_audio_playback_message
            )
        )

    def on_audio_playback_consumer_ready(self, consumer: RmqConsumer):
        self.audio_playback_consumer = consumer
        asyncio.create_task(self.process_audio_playback())

    def on_audio_playback_message(self, _unused_consumer: RmqConsumer, message: AudioMessage):
        self.audio_playback_queue.put_nowait(message)

    async def process_audio_playback(self):
        async for message in self.audio_playback_generator():
            LOGGER.info('TODO: implement processing of audio playback message.')

    async def audio_playback_generator(self):
        while True:
            yield await self.audio_playback_queue.get()


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
