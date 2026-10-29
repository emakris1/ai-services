import logging
import msgspec

from pika.exchange_type import ExchangeType
from pika.frame import Method
from pika.spec import BasicProperties
from typing import Callable, Generic, TypeVar

from ai_core.messages import enc_hook
from ai_core.rmq_base import RmqBase

LOGGER = logging.getLogger(__name__)

T = TypeVar("T", bound=msgspec.Struct)


class RmqProducer(RmqBase, Generic[T]):
    def __init__(
        self,
        exchange_name: str,
        exchange_type: ExchangeType,
        routing_key: str = '',
        on_producer_ready_callback: Callable[['RmqProducer'], None] = lambda _producer: None,
    ):
        super().__init__(exchange_name, exchange_type, routing_key)

        self.on_producer_ready_callback: Callable[['RmqProducer'], None] = on_producer_ready_callback

        self.producer_name: str = f'{self.exchange_name}:{self.routing_key}'

        self.deliveries: dict[int, bool] = {}
        self.acked: int = 0
        self.nacked: int = 0
        self.message_number: int = 0

        self.encoder: msgspec.json.Encoder = msgspec.json.Encoder(enc_hook=enc_hook)

    def post_exchange_declare(self) -> None:
        self.enable_delivery_confirmations()

    def enable_delivery_confirmations(self) -> None:
        LOGGER.debug('Enabling delivery confirmations for producer %s...', self.producer_name)
        self.channel.confirm_delivery(self.on_delivery_confirmation)

        LOGGER.info('Producer %s is ready to publish messages!', self.producer_name)
        self.on_producer_ready_callback(self)

    def on_delivery_confirmation(self, method_frame: Method) -> None:
        confirmation_type = method_frame.method.NAME.split('.')[1].lower()
        ack_multiple = method_frame.method.multiple
        delivery_tag = method_frame.method.delivery_tag

        LOGGER.debug('Producer %s received %s for delivery tag: %d (multiple: %s)',
                     self.producer_name, confirmation_type, delivery_tag, ack_multiple)

        if self.deliveries.pop(delivery_tag, None):
            if confirmation_type == 'ack':
                self.acked += 1
            elif confirmation_type == 'nack':
                self.nacked += 1

        if ack_multiple:
            for tmp_tag in list(self.deliveries.keys()):
                if tmp_tag <= delivery_tag:
                    if self.deliveries.pop(tmp_tag, None):
                        if confirmation_type == 'ack':
                            self.acked += 1
                        elif confirmation_type == 'nack':
                            self.nacked += 1

        # NOTE: at some point we should check self._deliveries for stale entries and decide to attempt re-delivery

        LOGGER.debug('Producer %s published %d messages; %d awaiting confirmation, %d were acked, and %d were nacked',
                     self.producer_name, self.message_number, len(self.deliveries), self.acked, self.nacked)

    def publish_message(self, message: T) -> None:
        if self.channel is None:
            LOGGER.warning('Channel has not yet been created for producer %s! Skipping publish of message.',
                           self.producer_name)
            return
        if not self.channel.is_open:
            LOGGER.warning('Channel is not open for producer %s! Skipping publish of message.', self.producer_name)
            return

        LOGGER.debug('Producer %s publishing message...', self.producer_name)
        self.channel.basic_publish(
            exchange=self.exchange_name,
            routing_key=self.routing_key,
            body=self.encoder.encode(message),
            properties=BasicProperties(
                app_id=f'{self.__class__.__name__}[{message.__class__.__name__}]',
                content_type='application/json'
            )
        )
        self.message_number += 1
        self.deliveries[self.message_number] = True
        LOGGER.debug('Producer %s Published message #%d!', self.producer_name, self.message_number)
