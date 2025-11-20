import asyncio
import logging
import numpy as np
import sounddevice as sd

from pika.exchange_type import ExchangeType
from typing import Any

from cgt_ai_core.log_config import LOG_FORMAT
from cgt_ai_core.messages import AudioMessage
from cgt_ai_core.rmq_producer import RmqProducer
from cgt_ai_core.rmq_service import RmqService
from cgt_ai_core.service_arg_parser import get_service_arg_parser

LOGGER = logging.getLogger(__name__)


class AudioCaptureService(RmqService):
    def __init__(self,
                 host: str = None,
                 port: int = None,
                 username: str = None,
                 password: str = None,
                 device_index: int = None,
                 channels: int = None,
                 sample_rate: int = None):
        super().__init__(host, port, username, password)

        if device_index is not None:
            self.device: dict = sd.query_devices(device_index)
        else:
            LOGGER.info('No audio device index provided. Sampling from default input audio device.')
            self.device: dict = sd.query_devices(kind='input')
        self.device_index: int = self.device['index']
        self.device_name: str = self.device['name']

        if channels is not None:
            self.channels: int = channels
        else:
            max_input_channels = self.device['max_input_channels']
            LOGGER.info(
                'No channel count provided. Sampling from audio device max of %d channel(s).',
                max_input_channels
            )
            self.channels: int = max_input_channels

        if sample_rate is not None:
            self.sample_rate: int = sample_rate
        else:
            default_sample_rate = int(self.device['default_samplerate'])
            LOGGER.info(
                'No sample rate provided. Sampling at audio device default of %d Hz.',
                default_sample_rate
            )
            self.sample_rate: int = default_sample_rate

        try:
            sd.check_input_settings(device=self.device_index, channels=self.channels, samplerate=self.sample_rate)
        except sd.PortAudioError as exc:
            LOGGER.exception('Invalid audio device settings', exc_info=exc)
            raise exc

        LOGGER.info(
            'Sampling %d channels at a rate of %d Hz from audio device {index: %d, name: %s}.',
            self.channels,
            self.sample_rate,
            self.device_index,
            self.device_name
        )

        self.audio_capture_producer: RmqProducer | None = None
        self.add_producer(
            RmqProducer(
                on_producer_ready_callback=self.on_audio_capture_producer_ready,
                connection_params=self.connection_params,
                exchange_name='audio_capture',
                exchange_type=ExchangeType.direct
            )
        )

    def on_audio_capture_producer_ready(self, producer: RmqProducer):
        self.audio_capture_producer = producer
        asyncio.create_task(self.sample_input_stream())

    async def sample_input_stream(self):
        async for input_stream_data in self.input_stream_generator():
            message = AudioMessage(
                sample_rate=self.sample_rate,
                samples=input_stream_data
            )
            LOGGER.info('Publishing audio capture message with %d samples.', input_stream_data.size)
            self.audio_capture_producer.publish_message(message)

    async def input_stream_generator(self):
        """Generator that yields blocks of input data as NumPy arrays."""
        q_in: asyncio.Queue[np.ndarray] = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def callback(indata: np.ndarray, frames: int, _unused_time: Any, _unused_status: sd.CallbackFlags):
            LOGGER.debug('Received %d frames of input stream data.', frames)
            try:
                loop.call_soon_threadsafe(q_in.put_nowait, indata.copy())
            except asyncio.QueueFull:
                LOGGER.warning('Input stream queue is full. Discarding input stream data.')
            except asyncio.QueueShutDown:
                LOGGER.warning('Input stream queue is shut down. Discarding input stream data.')

        input_stream = sd.InputStream(
            device=self.device_index,
            channels=self.channels,
            samplerate=self.sample_rate,
            dtype=np.float32,
            callback=callback
        )
        with input_stream:
            while True:
                yield await q_in.get()


async def main():
    parser = get_service_arg_parser(description='Audio Capture Service')
    device_group = parser.add_argument_group('Device Arguments')
    device_group.add_argument('-x', '--device-index', type=int, default=None,
                              help='Index of audio device to sample')
    device_group.add_argument('-m', '--device-prompt', action='store_true',
                              help='Show a prompt to select which audio device to sample from a list of available devices')
    sampling_group = parser.add_argument_group('Sampling Arguments')
    sampling_group.add_argument('-c', '--channels', type=int, default=None,
                                help='Number of channels to sample from audio device')
    sampling_group.add_argument('-s', '--sample-rate', type=int, default=None, help='Sample rate in Hz')
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level), format=LOG_FORMAT)

    if args.device_index is None:
        # index and prompt are mutually exclusive - only show prompt if an index is not provided
        if args.device_prompt:
            print(sd.query_devices())
            input_str = input('Enter index of audio device to sample (or press Enter for default): ').strip()
            try:
                args.device_index = int(input_str) if input_str else None
            except ValueError as exc:
                LOGGER.exception('Invalid audio device index provided.', exc_info=exc)
                args.device_index = None

    service = AudioCaptureService(
        host=args.rmq_host,
        port=args.rmq_port,
        username=args.rmq_username,
        password=args.rmq_password,
        device_index=args.device_index,
        channels=args.channels,
        sample_rate=args.sample_rate
    )
    await service.run()

if __name__ == '__main__':
    asyncio.run(main())
