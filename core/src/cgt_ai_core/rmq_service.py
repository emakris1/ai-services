import asyncio
import logging
import msgspec

from dataclasses import dataclass
from pika import ConnectionParameters
from pika.credentials import PlainCredentials
from pika.exchange_type import ExchangeType
from typing import Callable, Generic, Type, TypeVar

from cgt_ai_core.rmq_default_config import DefaultConnectionParameters
from cgt_ai_core.rmq_consumer import RmqConsumer
from cgt_ai_core.rmq_producer import RmqProducer

LOGGER = logging.getLogger(__name__)

T = TypeVar("T", bound=msgspec.Struct)


@dataclass
class RmqConsumerData:
    tag: str
    reference: RmqConsumer
    client_on_ready_callback: Callable[[RmqConsumer], None]
    ready_event: asyncio.Event


@dataclass
class RmqProducerData:
    tag: str
    reference: RmqProducer
    client_on_ready_callback: Callable[[RmqProducer], None]
    ready_event: asyncio.Event


class RmqService:
    def __init__(self,
                 host: str = None,
                 port: int = None,
                 username: str = None,
                 password: str = None):
        # all host/port/username/password arguments provided - initialize a new ConnectionParameters with arguments
        if all(arg is not None for arg in (host, port, username, password)):
            self.connection_params = ConnectionParameters(host=host, port=port, credentials=PlainCredentials(username, password))
        # any one of host/port/username/password provided - initialize with default ConnectionParameters and override specific arguments
        else:
            self.connection_params = DefaultConnectionParameters
            if host:
                self.connection_params.host = host
            if port:
                self.connection_params.port = port
            if username:
                self.connection_params.credentials.username = username
            if password:
                self.connection_params.credentials.password = password

        self.is_running = False

        self.consumers: dict[str, RmqConsumerData] = {}
        self.producers: dict[str, RmqProducerData] = {}

    def add_consumer(self,
                     message_type: Type[T],
                     exchange_name: str,
                     exchange_type: ExchangeType,
                     queue_name: str = '',
                     routing_key: str = '',
                     on_consumer_ready_callback: Callable[['RmqConsumer'], None] = lambda _consumer: None,
                     on_message_callback: Callable[['RmqConsumer[T]', T], None] = lambda _consumer, _message: None):
        if self.is_running:
            LOGGER.warning('Cannot add consumer while service is running. Please stop service first and then add consumer.')
            return

        consumer = RmqConsumer(
            message_type=message_type,
            connection_params=self.connection_params,
            exchange_name=exchange_name,
            exchange_type=exchange_type,
            queue_name=queue_name,
            routing_key=routing_key,
            on_consumer_ready_callback=self.on_consumer_ready,
            on_message_callback=on_message_callback
        )

        self.consumers[consumer.consumer_tag] = RmqConsumerData(
            tag=consumer.consumer_tag,
            reference=consumer,
            client_on_ready_callback=on_consumer_ready_callback,
            ready_event=asyncio.Event()
        )

    def add_producer(self,
                     exchange_name: str,
                     exchange_type: ExchangeType,
                     routing_key: str = '',
                     on_producer_ready_callback: Callable[['RmqProducer'], None] = lambda _producer: None):
        if self.is_running:
            LOGGER.warning('Cannot add producer while service is running. Please stop service first and then add producer.')
            return

        producer = RmqProducer(
            connection_params=self.connection_params,
            exchange_name=exchange_name,
            exchange_type=exchange_type,
            routing_key=routing_key,
            on_producer_ready_callback=self.on_producer_ready
        )

        self.producers[producer.producer_tag] = RmqProducerData(
            tag=producer.producer_tag,
            reference=producer,
            client_on_ready_callback=on_producer_ready_callback,
            ready_event=asyncio.Event()
        )

    def on_consumer_ready(self, consumer: RmqConsumer):
        if consumer.consumer_tag in self.consumers:
            consumer_data = self.consumers[consumer.consumer_tag]
            consumer_data.client_on_ready_callback(consumer)
            consumer_data.ready_event.set()

    def on_producer_ready(self, producer: RmqProducer):
        if producer.producer_tag in self.producers:
            producer_data = self.producers[producer.producer_tag]
            producer_data.client_on_ready_callback(producer)
            producer_data.ready_event.set()

    def on_service_ready(self):
        pass

    async def open_connections(self):
        LOGGER.info('Opening all connections...')
        for consumer_data in self.consumers.values():
            consumer_data.reference.open_connection()
        for producer_data in self.producers.values():
            producer_data.reference.open_connection()

        LOGGER.info('Waiting for all connections to finish opening...')
        consumer_wait_coros = [consumer_data.ready_event.wait() for consumer_data in self.consumers.values()]
        producer_wait_coros = [producer_data.ready_event.wait() for producer_data in self.producers.values()]
        await asyncio.gather(*consumer_wait_coros, *producer_wait_coros)

        LOGGER.info('All connections are open!')
        self.on_service_ready()

    async def close_connections(self):
        LOGGER.info('Closing all connections...')
        for consumer_data in self.consumers.values():
            consumer_data.reference.close_connection()
        for producer_data in self.producers.values():
            producer_data.reference.close_connection()
        LOGGER.info('All connections are closed!')

    async def run(self):
        LOGGER.info('Running...')
        consumer_run_coros = [consumer_data.reference.run() for consumer_data in self.consumers.values()]
        producer_run_coros = [producer_data.reference.run() for producer_data in self.producers.values()]
        self.is_running = True
        try:
            await self.open_connections()
            await asyncio.gather(*consumer_run_coros, *producer_run_coros)
        except asyncio.CancelledError as exc:
            LOGGER.exception('Run cancelled.', exc_info=exc)
        except Exception as exc:
            LOGGER.exception('Unhandled exception.', exc_info=exc)

    async def stop(self):
        LOGGER.info('Stopping...')
        consumer_stop_coros = [consumer_data.reference.stop() for consumer_data in self.consumers.values()]
        producer_stop_coros = [producer_data.reference.stop() for producer_data in self.producers.values()]
        try:
            await asyncio.gather(*consumer_stop_coros, *producer_stop_coros)
            await self.close_connections()
        except asyncio.CancelledError as exc:
            LOGGER.exception('Stop cancelled.', exc_info=exc)
        except Exception as exc:
            LOGGER.exception('Unhandled exception.', exc_info=exc)
        self.is_running = False
        LOGGER.info('Stop completed.')
