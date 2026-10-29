import asyncio
import logging
import numpy as np
import sounddevice as sd
import time

from threading import Lock
from pika.exchange_type import ExchangeType
from typing import Any

from ai_common.log_config import LOG_FORMAT
from ai_common.messages import AudioMessage, StopListeningMessage
from ai_common.service_arg_parser import get_service_arg_parser
from ai_rmq.consumer import RmqConsumer
from ai_rmq.producer import RmqProducer
from ai_rmq.runner import run_service
from ai_rmq.service import RmqService

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

        self.event_loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
        self.input_stream_queue: asyncio.Queue[np.ndarray] = asyncio.Queue()
        self.sample_input_stream_task: asyncio.Task | None = None

        self.lock: Lock = Lock()
        self.stop_listening_duration: float = 0.0
        self.last_duration_update_time: float = 0.0

        self.audio_capture_producer: RmqProducer | None = None
        self.add_producer(
            exchange_name='audio_capture',
            exchange_type=ExchangeType.direct,
            on_producer_ready_callback = self.on_audio_capture_producer_ready
        )

        self.stop_listening_consumer: RmqConsumer | None = None
        self.add_consumer(
            message_type=StopListeningMessage,
            exchange_name='stop_listening',
            exchange_type=ExchangeType.direct,
            on_consumer_ready_callback=self.on_stop_listening_consumer_ready,
            on_message_callback=self.on_stop_listening_message
        )

    def on_audio_capture_producer_ready(self, producer: RmqProducer):
        self.audio_capture_producer = producer

    def on_service_ready(self):
        super().on_service_ready()
        self.sample_input_stream_task = asyncio.create_task(self.sample_input_stream())

    async def sample_input_stream(self):
        async for input_stream_data in self.input_stream_generator():
            message = AudioMessage(
                sample_rate=self.sample_rate,
                samples=input_stream_data
            )
            LOGGER.info('Publishing audio capture message with %d samples.', input_stream_data.size)
            self.audio_capture_producer.publish_message(message)

    async def input_stream_generator(self):

        def callback(indata: np.ndarray, frames: int, _unused_time: Any, _unused_status: sd.CallbackFlags):
            if not self.lock.acquire(blocking=False):
                LOGGER.debug('Could not acquire lock for input stream buffer. Discarding input stream data.')
                return
            if self.stop_listening_duration > 0.0:
                LOGGER.info('Stop listening is active for %.2f more second(s). Discarding input stream data.',
                            self.stop_listening_duration)
                current_time = time.monotonic()
                duration = current_time - self.last_duration_update_time
                self.stop_listening_duration = max(self.stop_listening_duration - duration, 0.0)
                self.last_duration_update_time = current_time
                self.lock.release()
                return
            else:
                self.lock.release()

            LOGGER.debug('Received %d frames of input stream data.', frames)
            try:
                self.event_loop.call_soon_threadsafe(self.input_stream_queue.put_nowait, indata.copy())
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
                yield await self.input_stream_queue.get()

    def on_stop_listening_consumer_ready(self, consumer: RmqConsumer):
        self.stop_listening_consumer = consumer

    def on_stop_listening_message(self, _unused_consumer: RmqConsumer, message: StopListeningMessage):
        LOGGER.info('Received stop listening message. Dropping audio captures for an (additional) %.2f second(s).',
                    message.duration)
        self.lock.acquire()
        self.stop_listening_duration += message.duration
        self.last_duration_update_time = time.monotonic()
        self.lock.release()


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
    run_service(main())
