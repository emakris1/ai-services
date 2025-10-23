import json
import logging

from typing import Any
from typing import Callable

from pika import ConnectionParameters
from pika.channel import Channel
from pika.exchange_type import ExchangeType
from pika.frame import Method
from pika.spec import BasicProperties
from pika.spec import Basic

from cgt_ai_core.rmq_base import RmqBase

LOGGER = logging.getLogger(__name__)


class RmqConsumer(RmqBase):
    def __init__(self,
                 on_message_callback: Callable[[str, str, str, Any], None],
                 connection_params: ConnectionParameters,
                 exchange_name: str,
                 exchange_type: ExchangeType,
                 queue_name: str = '',
                 routing_key: str = None):
        super().__init__(connection_params, exchange_name, exchange_type, queue_name, routing_key)

        self.on_message_callback = on_message_callback

        self._consumer_tag = None

        self._prefetch_count = 0
        self._prefetch_size = 0

    def post_queue_bind(self):
        self.set_qos()

    def set_qos(self):
        LOGGER.info('Configuring QoS with prefetch size of %d and prefetch count of %d...',
                    self._prefetch_size, self._prefetch_count)
        self._channel.basic_qos(
            prefetch_size=self._prefetch_size,
            prefetch_count=self._prefetch_count,
            callback=self.on_basic_qos_ok
        )

    def on_basic_qos_ok(self, _unused_method_frame: Method):
        LOGGER.info('QOS configured with prefetch size of %d and prefetch count of %d!',
                    self._prefetch_size, self._prefetch_count)
        self.start_consuming()

    def start_consuming(self):
        LOGGER.info('Starting message consumption...')
        self._channel.add_on_cancel_callback(self.on_consumer_cancelled)
        self._consumer_tag = self._channel.basic_consume(queue=self.queue_name, on_message_callback=self.on_message)

    def on_consumer_cancelled(self, method_frame: Method):
        LOGGER.error('Consumer %s was cancelled remotely, shutting down...', method_frame.method.consumer_tag)
        self.close_connection()

    def on_message(self,
                   _unused_channel: Channel,
                   basic_deliver: Basic.Deliver,
                   basic_properties: BasicProperties,
                   body: bytes):
        json_body = json.loads(body)
        LOGGER.info('Received message # %s from %s: %s',
                    basic_deliver.delivery_tag, basic_properties.app_id, json_body)
        self.on_message_callback(self.exchange_name, self.queue_name, self.routing_key, json_body)
        self.acknowledge_message(basic_deliver.delivery_tag)

    def acknowledge_message(self, delivery_tag: int):
        LOGGER.info('Acknowledging message %s...', delivery_tag)
        self._channel.basic_ack(delivery_tag)

    def stop_consuming(self):
        LOGGER.info('Stopping message consumption for consumer %s...', self._consumer_tag)
        self._channel.basic_cancel(self._consumer_tag, self.on_cancel_ok)

    def on_cancel_ok(self, method_frame: Method):
        LOGGER.info('Consumer %s was cancelled successfully. Message consumption stopped.', method_frame.method.consumer_tag)
        self.close_channel()

    def pre_close_connection(self):
        self.stop_consuming()
