import logging
import msgspec

from pika import ConnectionParameters
from pika.channel import Channel
from pika.exchange_type import ExchangeType
from pika.frame import Method
from pika.spec import BasicProperties
from pika.spec import Basic
from typing import Callable, Generic, Type, TypeVar

from cgt_ai_core.messages import dec_hook
from cgt_ai_core.rmq_base import RmqBase

LOGGER = logging.getLogger(__name__)

T = TypeVar("T", bound=msgspec.Struct)


class RmqConsumer(RmqBase, Generic[T]):
    def __init__(self,
                 message_type: Type[T],
                 connection_params: ConnectionParameters,
                 exchange_name: str,
                 exchange_type: ExchangeType,
                 queue_name: str = '',
                 routing_key: str = '',
                 on_consumer_ready_callback: Callable[['RmqConsumer'], None] = lambda _consumer: None,
                 on_message_callback: Callable[['RmqConsumer[T]', T], None] = lambda _consumer, _message: None):
        super().__init__(connection_params, exchange_name, exchange_type, routing_key)

        self.message_type = message_type
        self.queue_name = queue_name

        self.on_consumer_ready_callback = on_consumer_ready_callback
        self.on_message_callback = on_message_callback

        self.consumer_tag = f'{self.exchange_name}:{self.routing_key}:{self.queue_name}'

        self.prefetch_count = 0
        self.prefetch_size = 0

        self.decoder = msgspec.json.Decoder(type=self.message_type, dec_hook=dec_hook)

    def post_exchange_declare(self):
        self.declare_queue()

    def declare_queue(self):
        LOGGER.debug('Declaring queue "%s"...', self.queue_name if self.queue_name else 'anonymous')
        self.channel.queue_declare(queue=self.queue_name, callback=self.on_queue_declare_ok)

    def on_queue_declare_ok(self, method_frame: Method):
        assigned_queue_name = method_frame.method.queue
        # Update self.queue_name if it was assigned anonymously
        if not self.queue_name:
            self.queue_name = assigned_queue_name
        LOGGER.debug('Queue "%s" declared!', self.queue_name)
        self.bind_queue()

    def bind_queue(self):
        LOGGER.debug('Binding queue "%s" to exchange "%s" with routing key "%s"...',
                     self.queue_name, self.exchange_name, self.routing_key or 'default')
        self.channel.queue_bind(
            queue=self.queue_name,
            exchange=self.exchange_name,
            routing_key=self.routing_key,
            callback=self.on_queue_bind_ok
        )

    def on_queue_bind_ok(self, _unused_method_frame: Method):
        if not self.routing_key:
            self.routing_key = 'default'
        LOGGER.debug('Queue "%s" successfully bound to exchange "%s" with routing key "%s"!',
                     self.queue_name, self.exchange_name, self.routing_key)
        self.set_qos()

    def set_qos(self):
        LOGGER.debug('Configuring QoS with prefetch size of %d and prefetch count of %d...',
                     self.prefetch_size, self.prefetch_count)
        self.channel.basic_qos(
            prefetch_size=self.prefetch_size,
            prefetch_count=self.prefetch_count,
            callback=self.on_basic_qos_ok
        )

    def on_basic_qos_ok(self, _unused_method_frame: Method):
        LOGGER.debug('QOS configured with prefetch size of %d and prefetch count of %d!',
                     self.prefetch_size, self.prefetch_count)
        self.start_consuming()

    def start_consuming(self):
        LOGGER.debug('Starting message consumption...')

        self.channel.add_on_cancel_callback(self.on_consumer_cancelled)
        consumer_tag = self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=self.on_message,
            consumer_tag=self.consumer_tag
        )
        if consumer_tag != self.consumer_tag:
            LOGGER.error('Consumer tag mismatch! Expected %s but got %s!', self.consumer_tag, consumer_tag)
            self.channel.basic_cancel(consumer_tag, self.on_cancel_ok)
            return

        LOGGER.info('Consumer %s is ready to consume messages!', self.consumer_tag)
        self.on_consumer_ready_callback(self)

    def on_consumer_cancelled(self, method_frame: Method):
        LOGGER.error('Consumer %s was cancelled remotely, shutting down...', method_frame.method.consumer_tag)
        self.close_connection()

    def on_message(self,
                   _unused_channel: Channel,
                   basic_deliver: Basic.Deliver,
                   basic_properties: BasicProperties,
                   body: bytes):
        message = self.decoder.decode(body)
        LOGGER.debug('Received message #%d from %s',
                     basic_deliver.delivery_tag, basic_properties.app_id)
        self.on_message_callback(self, message)
        self.acknowledge_message(basic_deliver.delivery_tag)

    def acknowledge_message(self, delivery_tag: int):
        LOGGER.debug('Acknowledging message #%d...', delivery_tag)
        self.channel.basic_ack(delivery_tag)

    def stop_consuming(self):
        LOGGER.debug('Stopping message consumption for consumer %s...', self.consumer_tag)
        self.channel.basic_cancel(self.consumer_tag, self.on_cancel_ok)

    def on_cancel_ok(self, method_frame: Method):
        LOGGER.debug('Consumer %s was cancelled successfully. Message consumption stopped.', method_frame.method.consumer_tag)
        self.close_channel()

    def pre_close_connection(self):
        self.stop_consuming()
