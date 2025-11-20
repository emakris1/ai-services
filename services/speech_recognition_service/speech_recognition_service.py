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
from cgt_ai_core.messages import AudioMessage, SpeechRecognitionMessage
from cgt_ai_core.rmq_consumer import RmqConsumer
from cgt_ai_core.rmq_producer import RmqProducer
from cgt_ai_core.rmq_service import RmqService
from cgt_ai_core.service_arg_parser import get_service_arg_parser


LOGGER = logging.getLogger(__name__)


class SpeechRecognitionService(RmqService):
    def __init__(self,
                 host: str = None,
                 port: int = None,
                 username: str = None,
                 password: str = None):
        super().__init__(host, port, username, password)

        self.audio_capture_queue: asyncio.Queue[AudioMessage] = asyncio.Queue()

        self.dtype: np.dtype[np.float32] = np.float32
        self.sample_rate: int = 16000 # most ASR libraries expect 16kHz audio
        self.max_samples: int = self.sample_rate * 30 # only keep the most recent 30s of samples
        self.sample_window_size: int = 512

        self.samples: np.ndarray = np.empty(shape=0, dtype=self.dtype)
        self.samples_processed: int = 0
        self.detection_start_time: float | None = None
        self.detection_end_time: float | None = None
        self.transcription_segments: list[Segment] | None = None
        self.transcription_info: TranscriptionInfo | None = None

        self.audio_capture_consumer: RmqConsumer | None = None
        self.add_consumer(
            RmqConsumer(
                message_type=AudioMessage,
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
                routing_key='actor_commands_service',
                on_producer_ready_callback=self.on_speech_recognition_producer_ready
            )
        )

        self.silero_iterator = silero_vad.VADIterator(
            model=silero_vad.load_silero_vad(),
            min_silence_duration_ms=250,
            speech_pad_ms=500,
        )

        self.whisper_model = WhisperModel(model_size_or_path='turbo', device='cuda')

    def on_audio_capture_consumer_ready(self, consumer: RmqConsumer):
        self.audio_capture_consumer = consumer

    def on_audio_capture_message(self, _unused_consumer: RmqConsumer, message: AudioMessage):
        self.audio_capture_queue.put_nowait(message)

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

    def append_samples(self, message: AudioMessage):
        shaped_buffer = message.samples

        # if the audio capture has multiple channels, we need to average down to one channel
        # most ASR libraries including silero and whisper expect mono 16kHz audio
        if message.channels > 1:
            LOGGER.debug('Audio has %d channels, averaging down to mono.', message.channels)
            # average samples across channel axis
            mono_buffer = shaped_buffer.mean(axis=1, dtype=self.dtype)
        else:
            mono_buffer = shaped_buffer

        # if the audio capture has a sample rate other than 16kHz, we need to resample to 16kHz
        # most ASR libraries including silero and whisper expect mono 16kHz audio
        if message.sample_rate != self.sample_rate:
            LOGGER.debug('Audio has %dkHz sample rate, resampling to %dkHz.',
                         message.sample_rate/1000, self.sample_rate/1000)
            resampled_buffer = resampy.resample(x=mono_buffer, sr_orig=message.sample_rate, sr_new=self.sample_rate)
        else:
            resampled_buffer = mono_buffer

        self.samples = np.concatenate((self.samples, resampled_buffer))

        if self.detection_start_time is None and self.samples.size > self.max_samples:
            LOGGER.info('Exceeded max sample size, forcing a reset.')
            self.reset(force=True)

    def detect_speech(self):
        start_key = 'start'
        end_key = 'end'

        first_index = self.samples_processed
        last_index = self.samples_processed + self.sample_window_size

        while last_index <= self.samples.size:
            chunk = self.samples[first_index:last_index]
            chunk_tensor = torch.from_numpy(chunk)
            detections = self.silero_iterator(chunk_tensor, return_seconds=True)

            if detections:
                if start_key in detections:
                    self.detection_end_time = None
                    self.detection_start_time = detections[start_key]
                    LOGGER.info('Started detecting speech at buffer time %.2fs.', self.detection_start_time)
                if end_key in detections:
                    self.detection_end_time = detections[end_key]
                    LOGGER.info('Stopped detecting speech at buffer time %.2fs.', self.detection_end_time)

            self.samples_processed += self.sample_window_size
            first_index = self.samples_processed
            last_index = self.samples_processed + self.sample_window_size

    def transcribe_speech(self):
        if self.detection_start_time is None or self.detection_end_time is None:
            return

        segment_generator, transcription_info = self.whisper_model.transcribe(
            audio=self.samples,
            clip_timestamps=[self.detection_start_time, self.detection_end_time]
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

    def reset(self, force: bool = False):
        if not force and (not self.transcription_segments or not self.transcription_info):
            return

        self.samples = np.empty(shape=0, dtype=self.dtype)
        self.samples_processed = 0
        self.detection_start_time = None
        self.detection_end_time = None
        self.transcription_segments = None
        self.transcription_info = None
        self.silero_iterator.reset_states()


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
    await service.run()

if __name__ == '__main__':
    asyncio.run(main())
