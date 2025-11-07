import asyncio
import logging

from pika.exchange_type import ExchangeType

from cgt_ai_core.log_config import LOG_FORMAT
from cgt_ai_core.rmq_consumer import RmqConsumer
from cgt_ai_core.service import Service
from cgt_ai_core.service_arg_parser import get_service_arg_parser
from cgt_ai_core.service_runner import run_service

import messages as m
import command_embedder as ce


LOGGER = logging.getLogger(__name__)


class ActorCommandsService(Service):
    def __init__(self,
                 host: str = None,
                 port: int = None,
                 username: str = None,
                 password: str = None,
                 routing_key: str = ''):
        super().__init__(host, port, username, password)

        self.routing_key = routing_key

        self.add_consumer(
            RmqConsumer(
                connection_params=self.connection_params,
                exchange_name='actor_commands',
                routing_key=self.routing_key,
                exchange_type=ExchangeType.direct,
                on_message_callback=self.on_receive_command_config
            )
        )

        self.embedder = ce.CommandEmbedder()

    def on_receive_command_config(self, _, message: m.CommandConfig):
        config = m.dict_to_command_config(message)
        self.embedder.update_config(config)
        action, score = self.embedder.match_phrase_to_action("Fire!", m.Actor.GUNNER)
        print(action, score)

async def main():
    parser = get_service_arg_parser(description='Actor Commands Service')
    parser.add_argument_group('Subscription Arguments')
    parser.add_argument('-r', '--routing-key', default='actor_commands_service',
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
    await run_service(service)

if __name__ == '__main__':
    asyncio.run(main())
