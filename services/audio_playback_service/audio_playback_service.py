import asyncio
import logging
import numpy as np
import resampy
import sounddevice as sd

from threading import Lock
from pika.exchange_type import ExchangeType
from typing import Any

from cgt_ai_core.log_config import LOG_FORMAT
from cgt_ai_core.messages import AudioMessage, StopListeningMessage
from cgt_ai_core.rmq_consumer import RmqConsumer
from cgt_ai_core.rmq_producer import RmqProducer
from cgt_ai_core.rmq_service import RmqService
from cgt_ai_core.service_arg_parser import get_service_arg_parser

LOGGER = logging.getLogger(__name__)


class AudioPlaybackService(RmqService):
    def __init__(self,
                 host: str = None,
                 port: int = None,
                 username: str = None,
                 password: str = None,
                 device_index: int = None,
                 sample_rate: int = None):
        super().__init__(host, port, username, password)

        if device_index is not None:
            self.device: dict = sd.query_devices(device_index)
        else:
            LOGGER.info('No audio device index provided. Playing on default output audio device.')
            self.device: dict = sd.query_devices(kind='output')
        self.device_index: int = self.device['index']
        self.device_name: str = self.device['name']

        self.channels: int = 2 # only stereo audio supported

        if sample_rate is not None:
            self.sample_rate: int = sample_rate
        else:
            default_sample_rate = int(self.device['default_samplerate'])
            LOGGER.info(
                'No sample rate provided. Playing at audio device default of %d Hz.',
                default_sample_rate
            )
            self.sample_rate: int = default_sample_rate

        try:
            sd.check_output_settings(device=self.device_index, channels=self.channels, samplerate=self.sample_rate)
        except sd.PortAudioError as exc:
            LOGGER.exception('Invalid audio device settings', exc_info=exc)
            raise exc

        LOGGER.info(
            'Playing %d channels at a rate of %d Hz on audio device {index: %d, name: %s}.',
            self.channels,
            self.sample_rate,
            self.device_index,
            self.device_name
        )

        self.dtype: np.dtype[np.float32] = np.float32
        self.audio_playback_queue: asyncio.Queue[AudioMessage] = asyncio.Queue()
        self.output_stream_buffer: np.ndarray[tuple[int, int], np.dtype[np.float32]] = np.empty(
            shape=(0, self.channels), dtype=self.dtype)

        self.lock: Lock = Lock()

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

        self.stop_listening_producer: RmqProducer | None = None
        self.add_producer(
            RmqProducer(
                on_producer_ready_callback=self.on_stop_listening_producer_ready,
                connection_params=self.connection_params,
                exchange_name='stop_listening',
                exchange_type=ExchangeType.direct
            )
        )

    def on_audio_playback_consumer_ready(self, consumer: RmqConsumer):
        self.audio_playback_consumer = consumer
        asyncio.gather(self.process_audio_playback(), self.play_output_stream())

    def on_audio_playback_message(self, _unused_consumer: RmqConsumer, message: AudioMessage):
        try:
            self.audio_playback_queue.put_nowait(message)
        except asyncio.QueueFull:
            LOGGER.warning('Audio playback queue is full. Discarding audio message.')
        except asyncio.QueueShutDown:
            LOGGER.warning('Audio playback queue is shut down. Discarding audio message.')

    def on_stop_listening_producer_ready(self, producer: RmqProducer):
        self.stop_listening_producer = producer

    async def process_audio_playback(self):
        async for message in self.audio_playback_generator():
            self.append_samples(message)
            self.send_stop_listening(message)

    async def audio_playback_generator(self):
        while True:
            yield await self.audio_playback_queue.get()

    def append_samples(self, message: AudioMessage):
        shaped_buffer = message.samples

        # if the audio capture has multiple channels, we need to average down to one channel
        if shaped_buffer.ndim > 1:
            LOGGER.debug('Audio has %d channels, averaging down to mono.', shaped_buffer.ndim)
            # average samples across channel axis
            mono_buffer = shaped_buffer.mean(axis=1, dtype=self.dtype)
        else:
            mono_buffer = shaped_buffer.flatten()

        # if the audio capture has a sample rate other than the output audio device sample rate,
        # we need to resample to the output audio device sample rate
        if message.sample_rate != self.sample_rate:
            LOGGER.debug('Audio has %dkHz sample rate, resampling to %dkHz.',
                         message.sample_rate/1000, self.sample_rate/1000)
            resampled_buffer = resampy.resample(x=mono_buffer, sr_orig=message.sample_rate, sr_new=self.sample_rate)
        else:
            resampled_buffer = mono_buffer

        # Expand mono to stereo for a better playback experience
        stereo_buffer = np.column_stack((resampled_buffer, resampled_buffer)).astype(self.dtype, copy=False)

        self.lock.acquire()
        self.output_stream_buffer = np.concatenate((self.output_stream_buffer, stereo_buffer))
        self.lock.release()

    async def play_output_stream(self):
        stop_event = asyncio.Event()

        def callback(outdata: np.ndarray, _unused_frames: int, _unused_time: Any, _unused_status: sd.CallbackFlags):
            if not self.lock.acquire(blocking=False):
                LOGGER.debug('Could not acquire lock for output stream buffer - zero fill (silence)')
                outdata.fill(0)
                return

            frames_needed = outdata.shape[0]
            frames_available = self.output_stream_buffer.shape[0]

            if frames_available >= frames_needed:
                LOGGER.info('Output stream buffer has all frames available - full fill')
                outdata[:, :] = self.output_stream_buffer[:frames_needed, :]
                self.output_stream_buffer = self.output_stream_buffer[frames_needed:, :]
            elif frames_available > 0:
                LOGGER.info('Output stream buffer has some frames available - partial fill')
                outdata[:frames_available, :] = self.output_stream_buffer[:frames_available, :]
                outdata[frames_available:, :] = 0
                self.output_stream_buffer = self.output_stream_buffer[:0, :]
            else:
                LOGGER.debug('Output stream buffer has no frames available - zero fill (silence)')
                outdata.fill(0)

            self.lock.release()

        output_stream = sd.OutputStream(
            device=self.device_index,
            channels=self.channels,
            samplerate=self.sample_rate,
            dtype=np.float32,
            callback=callback
        )
        with output_stream:
            await stop_event.wait()

    def send_stop_listening(self, message: AudioMessage):
        duration = message.samples.shape[0] / message.sample_rate
        message = StopListeningMessage(duration=duration)
        LOGGER.info('Publishing stop listening message: %s', message)
        self.stop_listening_producer.publish_message(message)


async def main():
    parser = get_service_arg_parser(description='Audio Playback Service')
    device_group = parser.add_argument_group('Device Arguments')
    device_group.add_argument('-x', '--device-index', type=int, default=None,
                              help='Index of audio device to play on')
    device_group.add_argument('-m', '--device-prompt', action='store_true',
                              help='Show a prompt to select which audio device to play on from a list of available devices')
    playback_group = parser.add_argument_group('Playback Arguments')
    playback_group.add_argument('-s', '--sample-rate', type=int, default=None, help='Sample rate in Hz')
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
        sample_rate=args.sample_rate
    )
    await service.run()

if __name__ == '__main__':
    asyncio.run(main())
