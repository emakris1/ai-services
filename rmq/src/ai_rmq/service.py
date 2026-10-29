import asyncio
import logging
import msgspec

from dataclasses import dataclass
from pika.exchange_type import ExchangeType
from typing import Callable, Type, TypeVar

from ai_rmq.connection import RmqConnection
from ai_rmq.consumer import RmqConsumer
from ai_rmq.producer import RmqProducer

LOGGER = logging.getLogger(__name__)

T = TypeVar("T", bound=msgspec.Struct)


@dataclass
class RmqConsumerData:
    name: str
    reference: RmqConsumer
    client_on_ready_callback: Callable[[RmqConsumer], None]
    ready_event: asyncio.Event


@dataclass
class RmqProducerData:
    name: str
    reference: RmqProducer
    client_on_ready_callback: Callable[[RmqProducer], None]
    ready_event: asyncio.Event


class RmqService:
    def __init__(
        self,
        host: str = None,
        port: int = None,
        username: str = None,
        password: str = None,
    ):
        self.is_running: bool = False
        self.is_stopping: bool = False
        self.stop_running_event: asyncio.Event = asyncio.Event()
        self.connection_closed_event: asyncio.Event = asyncio.Event()

        self.configure_channel_task: asyncio.Task | None = None
        self.stop_task: asyncio.Task | None = None

        self.connection: RmqConnection = RmqConnection(
            host=host,
            port=port,
            username=username,
            password=password,
            on_connection_closed_callback=self.on_connection_closed,
            on_channel_opened_callback=self.on_channel_opened,
        )
        self.consumers: dict[str, RmqConsumerData] = {}
        self.producers: dict[str, RmqProducerData] = {}

    def add_consumer(
        self,
        message_type: Type[T],
        exchange_name: str,
        exchange_type: ExchangeType,
        queue_name: str = '',
        routing_key: str = '',
        on_consumer_ready_callback: Callable[['RmqConsumer'], None] = lambda _consumer: None,
        on_message_callback: Callable[['RmqConsumer[T]', T], None] = lambda _consumer, _message: None,
    ) -> None:
        if self.is_running:
            LOGGER.warning('Cannot add consumer while service is running. Please stop service first and then add consumer.')
            return

        consumer = RmqConsumer(
            message_type=message_type,
            exchange_name=exchange_name,
            exchange_type=exchange_type,
            queue_name=queue_name,
            routing_key=routing_key,
            on_consumer_ready_callback=self.on_consumer_ready,
            on_message_callback=on_message_callback,
        )

        self.consumers[consumer.consumer_name] = RmqConsumerData(
            name=consumer.consumer_name,
            reference=consumer,
            client_on_ready_callback=on_consumer_ready_callback,
            ready_event=asyncio.Event(),
        )

    def add_producer(
        self,
        exchange_name: str,
        exchange_type: ExchangeType,
        routing_key: str = '',
        on_producer_ready_callback: Callable[['RmqProducer'], None] = lambda _producer: None
    ) -> None:
        if self.is_running:
            LOGGER.warning('Cannot add producer while service is running. Please stop service first and then add producer.')
            return

        producer = RmqProducer(
            exchange_name=exchange_name,
            exchange_type=exchange_type,
            routing_key=routing_key,
            on_producer_ready_callback=self.on_producer_ready
        )

        self.producers[producer.producer_name] = RmqProducerData(
            name=producer.producer_name,
            reference=producer,
            client_on_ready_callback=on_producer_ready_callback,
            ready_event=asyncio.Event()
        )

    async def run(self) -> None:
        if self.is_running:
            LOGGER.info('Service is already running.')
            return

        LOGGER.info('Running...')
        self.is_running = True
        self.connection.open_connection()

        try:
            await self.stop_running_event.wait()
        except asyncio.CancelledError as exc:
            LOGGER.exception('Run cancelled', exc_info=exc)
        except Exception as exc:
            LOGGER.exception('Unhandled exception', exc_info=exc)
        finally:
            await self.stop()
            self.is_running = False
            self.stop_running_event.clear()

        LOGGER.info('Run completed.')

    async def stop(self) -> None:
        if self.is_stopping:
            LOGGER.info('Service is already stopping.')
            return

        LOGGER.info('Stopping...')
        self.is_stopping = True
        self.stop_running_event.set()
        self.connection.close_connection()
        try:
            await asyncio.wait_for(self.connection_closed_event.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            LOGGER.warning('Timed out waiting for connection to close.')
        except asyncio.CancelledError as exc:
            LOGGER.exception('Stop cancelled', exc_info=exc)
        except Exception as exc:
            LOGGER.exception('Unhandled exception', exc_info=exc)
        finally:
            self.is_stopping = False
            self.connection_closed_event.clear()

        LOGGER.info('Stop completed.')

    async def configure_channel(self) -> None:
        LOGGER.debug('Configuring channel with all required exchanges and queues for all consumers and producers...')
        for consumer_data in self.consumers.values():
            consumer_data.reference.configure_channel(self.connection.channel)
        for producer_data in self.producers.values():
            producer_data.reference.configure_channel(self.connection.channel)

        LOGGER.debug('Waiting for all consumers and producers to finish configuring channel...')
        consumer_wait_coros = [consumer_data.ready_event.wait() for consumer_data in self.consumers.values()]
        producer_wait_coros = [producer_data.ready_event.wait() for producer_data in self.producers.values()]
        await asyncio.gather(*consumer_wait_coros, *producer_wait_coros)

        LOGGER.debug('Channel configured!')
        self.on_service_ready()

    def on_connection_opened(self) -> None:
        pass

    def on_connection_closed(self) -> None:
        self.connection_closed_event.set()
        if not self.is_stopping:
            self.stop_task = asyncio.create_task(self.stop())

    def on_channel_opened(self) -> None:
        self.configure_channel_task = asyncio.create_task(self.configure_channel())

    def on_channel_closed(self) -> None:
        pass

    def on_service_ready(self) -> None:
        pass

    def on_consumer_ready(self, consumer: RmqConsumer) -> None:
        if consumer.consumer_name in self.consumers:
            consumer_data = self.consumers[consumer.consumer_name]
            consumer_data.client_on_ready_callback(consumer)
            consumer_data.ready_event.set()

    def on_producer_ready(self, producer: RmqProducer) -> None:
        if producer.producer_name in self.producers:
            producer_data = self.producers[producer.producer_name]
            producer_data.client_on_ready_callback(producer)
            producer_data.ready_event.set()
