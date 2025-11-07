import asyncio
import logging
import numpy as np
import resampy
import silero_vad
import torch

from faster_whisper import WhisperModel
from faster_whisper.transcribe import Segment, TranscriptionInfo

from pika.exchange_type import ExchangeType

from cgt_ai_core.log_config import LOG_FORMAT
from cgt_ai_core.messages import AudioCaptureMessage, SpeechRecognitionMessage
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

        self.dtype: np.dtype[np.float32] = np.float32
        self.sample_rate: int = 16000 # most ASR libraries expect 16kHz so we always resample to this rate
        self.max_samples: int = self.sample_rate * 10 # only keep the most recent 10s of samples
        self.samples: np.ndarray = np.empty(shape=0, dtype=self.dtype)

        self.timestamps: list[float] = []

        self.transcription_segments: list[Segment] | None = None
        self.transcription_info: TranscriptionInfo | None = None

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

        self.whisper_model = WhisperModel(model_size_or_path='turbo', device='cuda')
        self.silero_model = silero_vad.load_silero_vad()

    def on_audio_capture_consumer_ready(self, consumer: RmqConsumer):
        self.audio_capture_consumer = consumer

    def on_audio_capture_message(self, _unused_consumer: RmqConsumer, message: AudioCaptureMessage):
        self.event_loop.call_soon_threadsafe(self.audio_capture_queue.put_nowait, message)

    def on_speech_recognition_producer_ready(self, producer: RmqProducer):
        self.speech_recognition_producer = producer
        asyncio.create_task(self.process_audio_captures())

    async def process_audio_captures(self):
            async for message in self.audio_capture_generator():
                self.append_samples(message)
                self.detect_speech()
                self.transcribe_speech()
                self.publish_speech()
                self.reset()

    async def audio_capture_generator(self):
        while True:
            yield await self.audio_capture_queue.get()

    def append_samples(self, message: AudioCaptureMessage):
        flat_buffer = np.frombuffer(buffer=message.samples, dtype=self.dtype)
        frames = flat_buffer.size // message.channels
        shaped_buffer = flat_buffer.reshape(frames, message.channels)
        mono_buffer = shaped_buffer.mean(axis=1, dtype=self.dtype)
        resampled_buffer = resampy.resample(x=mono_buffer, sr_orig=message.sample_rate, sr_new=self.sample_rate)
        self.samples = np.concatenate((self.samples, resampled_buffer))
        if self.samples.size > self.max_samples:
            self.samples = self.samples[-self.max_samples:]

    def detect_speech(self):
        if self.samples.size == 0:
            return

        tensor = torch.from_numpy(self.samples)
        timestamp_dicts = silero_vad.get_speech_timestamps(
            audio=tensor,
            model=self.silero_model,
            min_speech_duration_ms=1000,
            min_silence_duration_ms=1000,
            speech_pad_ms=500,
            return_seconds=True
        )

        if timestamp_dicts:
            LOGGER.debug('Detected speech at times: %s', timestamp_dicts)
            for timestamp_dict in timestamp_dicts:
                self.timestamps.append(timestamp_dict['start'])
                self.timestamps.append(timestamp_dict['end'])

    def transcribe_speech(self):
        if not self.timestamps:
            return

        segment_generator, transcription_info = self.whisper_model.transcribe(
            audio=self.samples,
            clip_timestamps=self.timestamps,
        )
        self.transcription_info = transcription_info
        # iterating the generator triggers the transcription
        self.transcription_segments = [segment for segment in segment_generator]

    def publish_speech(self):
        if not self.transcription_segments or not self.transcription_info:
            return

        message = SpeechRecognitionMessage(
            language=self.transcription_info.language,
            language_probability=self.transcription_info.language_probability,
            text=' '.join(s.text.lstrip() for s in self.transcription_segments)) # strip whisper's leading spaces

        LOGGER.info('Publishing speech recognition message:\n\t%s', message)
        self.speech_recognition_producer.publish_message(message)

    def reset(self):
        if not self.transcription_segments or not self.transcription_info:
            return

        self.samples = np.empty(shape=0, dtype=self.dtype)
        self.timestamps.clear()
        self.transcription_segments = None
        self.transcription_info = None


async def main():
    parser = get_service_arg_parser(description='Speech Recognition Service')
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level), format=LOG_FORMAT)
    logging.getLogger('faster_whisper').setLevel(logging.WARNING)

    service = SpeechRecognitionService(
        host=args.rmq_host,
        port=args.rmq_port,
        username=args.rmq_username,
        password=args.rmq_password,
    )
    await run_service(service)

if __name__ == '__main__':
    asyncio.run(main())
