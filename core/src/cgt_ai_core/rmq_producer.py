import logging
import msgspec

from typing import Callable, Generic, TypeVar

from pika import ConnectionParameters
from pika.exchange_type import ExchangeType
from pika.frame import Method
from pika.spec import BasicProperties

from cgt_ai_core.messages import enc_hook
from cgt_ai_core.rmq_base import RmqBase


LOGGER = logging.getLogger(__name__)

T = TypeVar("T", bound=msgspec.Struct)


class RmqProducer(RmqBase, Generic[T]):
    def __init__(self,
                 connection_params: ConnectionParameters,
                 exchange_name: str,
                 exchange_type: ExchangeType,
                 routing_key: str = '',
                 on_producer_ready_callback: Callable[['RmqProducer[T]'], None] = lambda _producer: None):
        super().__init__(connection_params, exchange_name, exchange_type, routing_key)

        self.producer_tag = f'{self.exchange_name}:{self.routing_key}'

        self.on_producer_ready_callback = on_producer_ready_callback

        self.deliveries = {}
        self.acked = None
        self.nacked = None
        self.message_number = None

        self.encoder = msgspec.json.Encoder(enc_hook=enc_hook)

    def post_exchange_declare(self):
        self.enable_delivery_confirmations()

    def enable_delivery_confirmations(self):
        LOGGER.debug('Enabling delivery confirmations for producer %s...', self.producer_tag)
        self.channel.confirm_delivery(self.on_delivery_confirmation)

        LOGGER.info('Producer %s is ready to publish messages!', self.producer_tag)
        self.on_producer_ready_callback(self)

    def on_delivery_confirmation(self, method_frame: Method):
        confirmation_type = method_frame.method.NAME.split('.')[1].lower()
        ack_multiple = method_frame.method.multiple
        delivery_tag = method_frame.method.delivery_tag

        LOGGER.debug('Producer %s received %s for delivery tag: %d (multiple: %s)',
                    self.producer_tag, confirmation_type, delivery_tag, ack_multiple)

        if confirmation_type == 'ack':
            self.acked += 1
        elif confirmation_type == 'nack':
            self.nacked += 1

        del self.deliveries[delivery_tag]

        if ack_multiple:
            for tmp_tag in list(self.deliveries.keys()):
                if tmp_tag <= delivery_tag:
                    self.acked += 1
                    del self.deliveries[tmp_tag]
        """
        NOTE: at some point you would check self._deliveries for stale
        entries and decide to attempt re-delivery
        """

        LOGGER.debug('Producer %s published %d messages; %d awaiting confirmation, %d were acked, and %d were nacked',
                     self.producer_tag, self.message_number, len(self.deliveries), self.acked, self.nacked)

    def publish_message(self, message: T):
        if self.channel is None:
            LOGGER.warning('Channel has not yet been created for producer %s! Skipping publish of message.',
                           self.producer_tag)
            return
        if not self.channel.is_open:
            LOGGER.warning('Channel is not open for producer %s! Skipping publish of message.', self.producer_tag)
            return

        LOGGER.debug('Producer %s publishing message...', self.producer_tag)
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
        LOGGER.debug('Published message #%d!', self.message_number)

    def pre_open_connection(self):
        self.deliveries = {}
        self.acked = 0
        self.nacked = 0
        self.message_number = 0
