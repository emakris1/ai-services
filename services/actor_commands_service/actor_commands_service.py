import asyncio
import logging

from pika.exchange_type import ExchangeType

import cgt_ai_core.tts_enums as tts

from cgt_ai_core.log_config import LOG_FORMAT
from cgt_ai_core.messages import SpeechRecognitionMessage, TTSRequestMessage
from cgt_ai_core.rmq_consumer import RmqConsumer
from cgt_ai_core.rmq_producer import RmqProducer
from cgt_ai_core.rmq_service import RmqService
from cgt_ai_core.service_arg_parser import get_service_arg_parser

import messages as m

from action_cross_encoder import ActionCrossEncoder

LOGGER = logging.getLogger(__name__)


class ActorCommandsService(RmqService):
    def __init__(self,
                 host: str = None,
                 port: int = None,
                 username: str = None,
                 password: str = None,
                 routing_key: str = '',
                 score_threshold: float = 0.65,
                 ):
        super().__init__(host, port, username, password)

        self.routing_key = routing_key
        self.score_threshold = score_threshold
        self.current_ai_actor = m.Actor.GUNNER

        self.add_consumer(
            RmqConsumer(
                message_type=SpeechRecognitionMessage,
                connection_params=self.connection_params,
                exchange_name='speech_recognition',
                routing_key=self.routing_key,
                exchange_type=ExchangeType.direct,
                on_message_callback=self.on_receive_speech_recognition,
            )
        )

        self.add_consumer(
            RmqConsumer(
                message_type=m.CommandConfigMessage,
                connection_params=self.connection_params,
                exchange_name='actor_commands',
                routing_key=self.routing_key,
                exchange_type=ExchangeType.direct,
                on_message_callback=self.on_receive_command_config
            )
        )

        self.add_consumer(
            RmqConsumer(
                message_type=m.CurrentActorMessage,
                connection_params=self.connection_params,
                exchange_name='current_actor',
                routing_key=self.routing_key,
                exchange_type=ExchangeType.direct,
                on_message_callback=self.on_receive_current_actor
            )
        )

        self.action_recognition_producer: RmqProducer | None = None
        self.add_producer(
            RmqProducer(
                connection_params=self.connection_params,
                exchange_name='action_recognition',
                exchange_type=ExchangeType.direct,
                routing_key='crew_member_service',
                on_producer_ready_callback=self.on_action_recognition_producer_ready
            )
        )

        self.tts_request_producer: RmqProducer | None = None
        self.add_producer(
            RmqProducer(
                connection_params=self.connection_params,
                exchange_name='tts_request',
                exchange_type=ExchangeType.direct,
                on_producer_ready_callback=self.on_tts_request_producer_ready
            )
        )

        self.ace = ActionCrossEncoder()
        self.speech_queue: asyncio.Queue[SpeechRecognitionMessage] = asyncio.Queue()
        self.voice_map: dict[m.Actor, int] = {}

    def on_receive_speech_recognition(self, _, message: SpeechRecognitionMessage):
        try:
            self.speech_queue.put_nowait(message)
        except asyncio.QueueFull:
            LOGGER.warning('Speech recognition queue is full. Discarding speech recognition message.')
        except asyncio.QueueShutDown:
            LOGGER.warning('Speech recognition queue is shut down. Discarding speech recognition message.')

    def on_receive_command_config(self, _, message: m.CommandConfigMessage):
        for ac in message.commands:
            self.voice_map[ac.actor] = ac.voice
            for command in ac.commands:
                self.ace.add_action_reply(ac.actor, command)
                self.tts_request_producer.publish_message(
                    TTSRequestMessage(
                        language=tts.Language.AMERICAN_ENGLISH,
                        voice=self.get_voice(ac.voice),
                        text=command.reply,
                        play_immediately=False
                    )
                )
        LOGGER.info("Loaded %d actions into action command encoder", len(self.ace))
        self.clear_speech_queue()

    def on_receive_current_actor(self, _, message: m.CurrentActorMessage):
        if message.actor == m.Actor.DRIVER:
            self.current_ai_actor = m.Actor.GUNNER
        elif message.actor == m.Actor.GUNNER:
            self.current_ai_actor = m.Actor.DRIVER
        LOGGER.info("AI now controls %s", self.current_ai_actor)

    def on_action_recognition_producer_ready(self, producer: RmqProducer):
        self.action_recognition_producer = producer
        asyncio.create_task(self.process_speech_recognition())

    def on_tts_request_producer_ready(self, producer: RmqProducer):
        self.tts_request_producer = producer

    async def process_speech_recognition(self):
        while True:
            message = await self.speech_queue.get()
            (action, reply), score = self.ace.classify(self.current_ai_actor, message.text, message.language)
            self.on_action_matched(message.text, action, reply, score)

    def on_action_matched(self, text, action, reply, score):
        LOGGER.info(f"Phrase \"{text}\", Score: {round(score, 2)}/1")
        if score > self.score_threshold:
            act_rec_msg = m.ActionRecognitionMessage(score=score, actor=self.current_ai_actor, action=action)
            LOGGER.info('Publishing action recognition message:\n\t%s', act_rec_msg)
            self.action_recognition_producer.publish_message(act_rec_msg)

            tts_req_msg = TTSRequestMessage(
                language=tts.Language.AMERICAN_ENGLISH,
                voice=self.get_current_voice(),
                text=reply
            )
            LOGGER.info('Publishing TTS request message:\n\t%s', tts_req_msg)
            self.tts_request_producer.publish_message(tts_req_msg)

    def clear_speech_queue(self):
        queue_empty = False
        while not queue_empty:
            try:
                self.speech_queue.get_nowait()
            except asyncio.QueueEmpty:
                queue_empty = True

    def get_current_voice(self) -> tts.Voice:
        return self.get_voice(self.voice_map[self.current_ai_actor])

    @staticmethod
    def get_voice(index: int) -> tts.Voice:
        voices = list(tts.Voice)
        return voices[0] if index >= len(voices) else voices[index]


async def main():
    parser = get_service_arg_parser(description='Actor Commands Service')
    parser.add_argument_group('Subscription Arguments')
    parser.add_argument('-r', '--routing-key',
                        default='actor_commands_service',
                        help='Routing key to subscribe to messages with')
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level), format=LOG_FORMAT)
    service = ActorCommandsService(
        routing_key=args.routing_key,
        host=args.rmq_host,
        port=args.rmq_port,
        username=args.rmq_username,
        password=args.rmq_password
    )
    await service.run()

if __name__ == '__main__':
    asyncio.run(main())
