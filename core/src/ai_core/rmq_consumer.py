import logging
import msgspec

from pika.channel import Channel
from pika.exchange_type import ExchangeType
from pika.frame import Method
from pika.spec import BasicProperties
from pika.spec import Basic
from typing import Callable, Generic, Type, TypeVar

from ai_core.messages import dec_hook
from ai_core.rmq_base import RmqBase

LOGGER = logging.getLogger(__name__)

T = TypeVar("T", bound=msgspec.Struct)


class RmqConsumer(RmqBase, Generic[T]):
    def __init__(
        self,
        message_type: Type[T],
        exchange_name: str,
        exchange_type: ExchangeType,
        queue_name: str = '',
        routing_key: str = '',
        on_consumer_ready_callback: Callable[['RmqConsumer'], None] = lambda _consumer: None,
        on_message_callback: Callable[['RmqConsumer[T]', T], None] = lambda _consumer, _message: None,
    ):
        super().__init__(exchange_name, exchange_type, routing_key)

        self.message_type: Type[T] = message_type
        self.queue_name: str = queue_name

        self.on_consumer_ready_callback: Callable[['RmqConsumer'], None] = on_consumer_ready_callback
        self.on_message_callback: Callable[['RmqConsumer[T]', T], None] = on_message_callback

        self.consumer_name: str = f'{self.exchange_name}:{self.routing_key if self.routing_key else 'auto'}:{self.queue_name if self.queue_name else 'anonymous'}'

        self.consumer_tag: str | None = None

        self.prefetch_count: int = 0
        self.prefetch_size: int = 0

        self.decoder: msgspec.json.Decoder = msgspec.json.Decoder(type=self.message_type, dec_hook=dec_hook)

    def post_exchange_declare(self) -> None:
        self.declare_queue()

    def declare_queue(self) -> None:
        LOGGER.debug('Declaring queue "%s"...', self.queue_name if self.queue_name else 'anonymous')
        self.channel.queue_declare(queue=self.queue_name, callback=self.on_queue_declare_ok)

    def on_queue_declare_ok(self, method_frame: Method) -> None:
        assigned_queue_name = method_frame.method.queue
        # Update self.queue_name if it was assigned anonymously
        if not self.queue_name:
            self.queue_name = assigned_queue_name
        LOGGER.debug('Queue "%s" declared!', self.queue_name)
        self.bind_queue()

    def bind_queue(self) -> None:
        LOGGER.debug('Binding queue "%s" to exchange "%s" with routing key "%s"...',
                     self.queue_name, self.exchange_name, self.routing_key or 'default')
        self.channel.queue_bind(
            queue=self.queue_name,
            exchange=self.exchange_name,
            routing_key=self.routing_key,
            callback=self.on_queue_bind_ok
        )

    def on_queue_bind_ok(self, _unused_method_frame: Method) -> None:
        if not self.routing_key:
            self.routing_key = 'default'
        LOGGER.debug('Queue "%s" successfully bound to exchange "%s" with routing key "%s"!',
                     self.queue_name, self.exchange_name, self.routing_key)
        self.set_qos()

    def set_qos(self) -> None:
        LOGGER.debug('Configuring QoS with prefetch size of %d and prefetch count of %d...',
                     self.prefetch_size, self.prefetch_count)
        self.channel.basic_qos(
            prefetch_size=self.prefetch_size,
            prefetch_count=self.prefetch_count,
            callback=self.on_basic_qos_ok
        )

    def on_basic_qos_ok(self, _unused_method_frame: Method) -> None:
        LOGGER.debug('QOS configured with prefetch size of %d and prefetch count of %d!',
                     self.prefetch_size, self.prefetch_count)
        self.start_consuming()

    def start_consuming(self) -> None:
        LOGGER.debug('Consumer %s starting message consumption...', self.consumer_name)
        self.consumer_tag = self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=self.on_message,
        )

        LOGGER.info('Consumer %s is ready to consume messages!', self.consumer_name)
        self.on_consumer_ready_callback(self)

    def on_message(
        self,
        _unused_channel: Channel,
        basic_deliver: Basic.Deliver,
        basic_properties: BasicProperties,
        body: bytes,
    ) -> None:
        message = self.decoder.decode(body)
        LOGGER.debug('Consumer %s received message #%d from %s',
                     self.consumer_name, basic_deliver.delivery_tag, basic_properties.app_id)
        self.on_message_callback(self, message)
        self.acknowledge_message(basic_deliver.delivery_tag)

    def acknowledge_message(self, delivery_tag: int) -> None:
        LOGGER.debug('Consumer %s Acknowledging message #%d...', self.consumer_name, delivery_tag)
        self.channel.basic_ack(delivery_tag)
