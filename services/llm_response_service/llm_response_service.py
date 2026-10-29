import asyncio
import logging
import re
import threading

from pathlib import Path

from pika.exchange_type import ExchangeType
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer

import ai_common.enums.tts as tts
import ai_common.messages as msg

from ai_common.log_config import LOG_FORMAT
from ai_common.service_arg_parser import get_service_arg_parser
from ai_rmq.producer import RmqProducer
from ai_rmq.runner import run_service
from ai_rmq.service import RmqService

LOGGER = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = (
    'You are a conversational partner in a voice-driven interactive training application. '
    'Everything you write is spoken aloud by a text-to-speech engine, so reply in one to three short, natural '
    'sentences and never use markdown, lists, emoji, code, or other formatting that cannot be spoken.'
)

# Splitting on whitespace after terminal punctuation lets the first sentence reach TTS while the rest of the reply is
# still generating, which is the bulk of the perceived latency for a spoken response.
SENTENCE_BOUNDARY = re.compile(r'(?<=[.!?])\s+')

# Small models occasionally emit markdown despite the system prompt, and Kokoro will try to pronounce the symbols.
UNSPEAKABLE_CHARACTERS = re.compile(r'[*_#`~]')


class LlmResponseService(RmqService):
    def __init__(self,
                 host: str = None,
                 port: int = None,
                 username: str = None,
                 password: str = None,
                 routing_key: str = '',
                 model_name: str = 'Qwen/Qwen3.5-2B',
                 voice: tts.Voice = tts.Voice.AMERICAN_FEMALE_HEART,
                 system_prompt: str = DEFAULT_SYSTEM_PROMPT,
                 max_history_turns: int = 10,
                 max_new_tokens: int = 256,
                 temperature: float = 0.7,
                 ):
        super().__init__(host, port, username, password)

        self.routing_key = routing_key
        self.voice = voice
        # Kokoro voice IDs are prefixed with the language code of the pipeline that can pronounce them
        self.language = tts.Language(voice.value[0])
        self.system_prompt = system_prompt
        self.max_history_turns = max_history_turns
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature

        self.add_consumer(
            message_type=msg.SpeechRecognitionMessage,
            exchange_name='speech_recognition',
            routing_key=self.routing_key,
            exchange_type=ExchangeType.direct,
            on_message_callback=self.on_receive_speech_recognition,
        )

        self.tts_request_producer: RmqProducer | None = None
        self.add_producer(
            exchange_name='tts_request',
            exchange_type=ExchangeType.direct,
            on_producer_ready_callback=self.on_tts_request_producer_ready
        )

        LOGGER.info('Loading model %s', model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name, dtype='auto').to('cuda')
        self._warm_up_model()

        # Alternating user/assistant messages, trimmed to whole turns so the history always starts with a user message
        self.history: list[dict[str, str]] = []

        self.speech_queue: asyncio.Queue[msg.SpeechRecognitionMessage] = asyncio.Queue()
        self.process_speech_recognition_task: asyncio.Task | None = None

    def on_receive_speech_recognition(self, _, message: msg.SpeechRecognitionMessage):
        try:
            self.speech_queue.put_nowait(message)
        except asyncio.QueueFull:
            LOGGER.warning('Speech recognition queue is full. Discarding speech recognition message.')
        except asyncio.QueueShutDown:
            LOGGER.warning('Speech recognition queue is shut down. Discarding speech recognition message.')

    def on_tts_request_producer_ready(self, producer: RmqProducer):
        self.tts_request_producer = producer

    def on_service_ready(self):
        super().on_service_ready()
        self.process_speech_recognition_task = asyncio.create_task(self.process_speech_recognition())

    async def process_speech_recognition(self):
        while True:
            message = await self.speech_queue.get()
            text = message.text.strip()
            if not text:
                continue
            LOGGER.info('Responding to "%s"', text)
            try:
                await self.respond(text)
            except Exception as exc:
                LOGGER.exception('Failed to generate response', exc_info=exc)

    async def respond(self, text: str):
        user_message = {'role': 'user', 'content': text}
        streamer = self.start_generation([{'role': 'system', 'content': self.system_prompt}, *self.history, user_message])

        reply = ''
        pending_text = ''
        # Pull tokens off the streamer in a worker thread so the event loop stays free to flush each TTS request to
        # RabbitMQ as soon as it is published, rather than all at once after generation finishes
        while (new_text := await asyncio.to_thread(next, streamer, None)) is not None:
            reply += new_text
            pending_text += new_text
            *complete_sentences, pending_text = SENTENCE_BOUNDARY.split(pending_text)
            for sentence in complete_sentences:
                self.publish_tts_request(sentence)
        self.publish_tts_request(pending_text)

        reply = reply.strip()
        LOGGER.info('Generated reply "%s"', reply)
        # History is only committed once the reply succeeds so a failed turn can't leave two user messages in a row
        self.history += [user_message, {'role': 'assistant', 'content': reply}]
        self.history = self.history[max(len(self.history) - self.max_history_turns * 2, 0):]

    def start_generation(self, messages: list[dict[str, str]]) -> TextIteratorStreamer:
        inputs = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            # Hybrid reasoning models (e.g. Qwen3) think by default, which adds seconds of silent latency before the
            # spoken reply; templates that don't recognize this flag ignore it
            enable_thinking=False,
            return_tensors='pt',
            return_dict=True,
        ).to(self.model.device)
        streamer = TextIteratorStreamer(self.tokenizer, skip_prompt=True, skip_special_tokens=True)

        def generate():
            try:
                self.model.generate(
                    **inputs,
                    streamer=streamer,
                    max_new_tokens=self.max_new_tokens,
                    do_sample=True,
                    temperature=self.temperature,
                    top_p=0.8,
                    top_k=20,
                )
            except Exception as exc:
                LOGGER.exception('Generation failed', exc_info=exc)
                # generate() only signals the end of the stream on success, so without this the consumer would wait
                # on the streamer forever
                streamer.end()

        threading.Thread(target=generate, daemon=True).start()
        return streamer

    def publish_tts_request(self, text: str):
        text = UNSPEAKABLE_CHARACTERS.sub('', text).strip()
        if not text:
            return
        tts_req_msg = msg.TTSRequestMessage(language=self.language, voice=self.voice, text=text)
        LOGGER.info('Publishing TTS request message:\n\t%s', tts_req_msg)
        self.tts_request_producer.publish_message(tts_req_msg)

    def _warm_up_model(self):
        # First pass is slow, so do a throwaway generation to warm up
        inputs = self.tokenizer.apply_chat_template(
            [{'role': 'user', 'content': 'Hello'}],
            add_generation_prompt=True,
            enable_thinking=False,
            return_tensors='pt',
            return_dict=True,
        ).to(self.model.device)
        self.model.generate(**inputs, max_new_tokens=4)


async def main():
    parser = get_service_arg_parser(description='LLM Response Service')
    subscription_group = parser.add_argument_group('Subscription Arguments')
    subscription_group.add_argument('-r', '--routing-key',
                                    default='llm_response_service',
                                    help='Routing key to subscribe to messages with')
    model_group = parser.add_argument_group('Model Arguments')
    model_group.add_argument('-m', '--model', default='Qwen/Qwen3.5-2B',
                             help='Hugging Face ID or local path of the chat model to generate responses with')
    model_group.add_argument('-t', '--temperature', type=float, default=0.7,
                             help='Sampling temperature; lower is more predictable, higher is more varied')
    model_group.add_argument('-n', '--max-new-tokens', type=int, default=256,
                             help='Maximum number of tokens to generate per response')
    model_group.add_argument('-k', '--max-history-turns', type=int, default=10,
                             help='Number of prior user/assistant exchanges to include as conversation context')
    prompt_group = model_group.add_mutually_exclusive_group()
    prompt_group.add_argument('-s', '--system-prompt', default=None,
                              help='System prompt that sets the persona and behavior of the model')
    prompt_group.add_argument('-f', '--system-prompt-file', type=Path, default=None,
                              help='Path to a text file containing the system prompt')
    speech_group = parser.add_argument_group('Speech Arguments')
    speech_group.add_argument('-v', '--voice', type=tts.Voice, default=tts.Voice.AMERICAN_FEMALE_HEART,
                              choices=list(tts.Voice), metavar='VOICE',
                              help='Kokoro voice ID to speak responses with (e.g. af_heart, am_michael, bf_emma)')
    args = parser.parse_args()

    if args.system_prompt_file is not None:
        system_prompt = args.system_prompt_file.read_text(encoding='utf-8').strip()
    elif args.system_prompt is not None:
        system_prompt = args.system_prompt
    else:
        system_prompt = DEFAULT_SYSTEM_PROMPT

    logging.basicConfig(level=getattr(logging, args.log_level), format=LOG_FORMAT)
    service = LlmResponseService(
        routing_key=args.routing_key,
        host=args.rmq_host,
        port=args.rmq_port,
        username=args.rmq_username,
        password=args.rmq_password,
        model_name=args.model,
        voice=args.voice,
        system_prompt=system_prompt,
        max_history_turns=args.max_history_turns,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
    )
    await service.run()

if __name__ == '__main__':
    run_service(main())
