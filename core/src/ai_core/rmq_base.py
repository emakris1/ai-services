import logging

from abc import ABC, abstractmethod
from pika.channel import Channel
from pika.exchange_type import ExchangeType
from pika.frame import Method

LOGGER = logging.getLogger(__name__)


class RmqBase(ABC):
    def __init__(
        self,
        exchange_name: str,
        exchange_type: ExchangeType,
        routing_key: str = '',
    ):
        self.exchange_name: str = exchange_name
        self.exchange_type: str = exchange_type
        self.routing_key: str = routing_key

        self.channel: Channel | None = None

    def configure_channel(self, channel: Channel):
        self.channel = channel
        self.declare_exchange()

    def declare_exchange(self) -> None:
        LOGGER.debug('Declaring exchange with name "%s" and type "%s"...', self.exchange_name, self.exchange_type)
        self.channel.exchange_declare(
            exchange=self.exchange_name,
            exchange_type=self.exchange_type,
            callback=self.on_exchange_declare_ok
        )

    def on_exchange_declare_ok(self, _unused_method_frame: Method) -> None:
        LOGGER.debug('Exchange "%s" declared!', self.exchange_name)
        self.post_exchange_declare()

    @abstractmethod
    def post_exchange_declare(self) -> None:
        pass
