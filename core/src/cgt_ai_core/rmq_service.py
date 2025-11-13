import asyncio
import logging

from pika import ConnectionParameters
from pika.credentials import PlainCredentials

from cgt_ai_core.rmq_default_config import DefaultConnectionParameters
from cgt_ai_core.rmq_consumer import RmqConsumer
from cgt_ai_core.rmq_producer import RmqProducer


LOGGER = logging.getLogger(__name__)


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
        self.consumers = []
        self.producers = []

    def add_consumer(self, consumer : RmqConsumer):
        if self.is_running:
            LOGGER.warning('Cannot add consumer while service is running. Please stop service first and then add consumer.')
        else:
            self.consumers.append(consumer)

    def add_producer(self, producer : RmqProducer):
        if self.is_running:
            LOGGER.warning('Cannot add producer while service is running. Please stop service first and then add producer.')
        else:
            self.producers.append(producer)

    async def run(self):
        LOGGER.info('Running...')
        run_coroutines = [consumer.run() for consumer in self.consumers] + [producer.run() for producer in self.producers]
        self.is_running = True
        try:
            await asyncio.gather(*run_coroutines)
        except asyncio.CancelledError as exc:
            LOGGER.exception('Run cancelled.', exc_info=exc)
        except Exception as exc:
            LOGGER.exception('Unhandled exception.', exc_info=exc)

    async def stop(self):
        LOGGER.info('Stopping...')
        stop_coroutines = [consumer.stop() for consumer in self.consumers] + [producer.stop() for producer in self.producers]
        try:
            await asyncio.gather(*stop_coroutines)
        except asyncio.CancelledError as exc:
            LOGGER.exception('Stop cancelled.', exc_info=exc)
        except Exception as exc:
            LOGGER.exception('Unhandled exception.', exc_info=exc)
        self.is_running = False
        LOGGER.info('Stop completed.')
