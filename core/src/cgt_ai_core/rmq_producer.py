import logging
import msgspec

from typing import Callable, Generic, TypeVar

from pika import ConnectionParameters
from pika.exchange_type import ExchangeType
from pika.frame import Method
from pika.spec import BasicProperties

from cgt_ai_core.rmq_base import RmqBase

LOGGER = logging.getLogger(__name__)

T = TypeVar("T", bound=msgspec.Struct)


class RmqProducer(RmqBase, Generic[T]):
    def __init__(self,
                 on_producer_ready_callback: Callable[['RmqProducer[T]'], None],
                 connection_params: ConnectionParameters,
                 exchange_name: str,
                 exchange_type: ExchangeType,
                 queue_name: str = '',
                 routing_key: str = None):
        super().__init__(connection_params, exchange_name, exchange_type, queue_name, routing_key)

        self.on_producer_ready_callback = on_producer_ready_callback

        self._deliveries = {}
        self._acked = None
        self._nacked = None
        self._message_number = None

        self.encoder = msgspec.json.Encoder()

    def post_queue_bind(self):
        self.enable_delivery_confirmations()
        self.on_producer_ready_callback(self)

    def enable_delivery_confirmations(self):
        LOGGER.info('Enabling delivery confirmations...')
        self._channel.confirm_delivery(self.on_delivery_confirmation)

    def on_delivery_confirmation(self, method_frame: Method):
        confirmation_type = method_frame.method.NAME.split('.')[1].lower()
        ack_multiple = method_frame.method.multiple
        delivery_tag = method_frame.method.delivery_tag

        LOGGER.info('Received %s for delivery tag: %i (multiple: %s)',
                    confirmation_type, delivery_tag, ack_multiple)

        if confirmation_type == 'ack':
            self._acked += 1
        elif confirmation_type == 'nack':
            self._nacked += 1

        del self._deliveries[delivery_tag]

        if ack_multiple:
            for tmp_tag in list(self._deliveries.keys()):
                if tmp_tag <= delivery_tag:
                    self._acked += 1
                    del self._deliveries[tmp_tag]
        """
        NOTE: at some point you would check self._deliveries for stale
        entries and decide to attempt re-delivery
        """

        LOGGER.info('Published %i messages; %i awaiting confirmation, %i were acked, and %i were nacked',
                    self._message_number, len(self._deliveries), self._acked, self._nacked)

    def publish_message(self, message: T):
        if self._channel is None:
            LOGGER.warning('Channel has not yet been created! Skipping publish of message.')
            return
        if not self._channel.is_open:
            LOGGER.warning('Channel is not open! Skipping publish of message.')
            return

        LOGGER.info('Publishing message %s...', message)
        self._channel.basic_publish(
            exchange=self.exchange_name,
            routing_key=self.routing_key,
            body=self.encoder.encode(message),
            properties=BasicProperties(app_id=self.__class__.__name__, content_type='application/json')
        )
        self._message_number += 1
        self._deliveries[self._message_number] = True
        LOGGER.info('Published message #%i with content %s!', self._message_number, message)

    def pre_open_connection(self):
        self._deliveries = {}
        self._acked = 0
        self._nacked = 0
        self._message_number = 0
