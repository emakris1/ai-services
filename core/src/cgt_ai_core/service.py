import asyncio
import logging

from pika import ConnectionParameters
from pika.credentials import PlainCredentials

from cgt_ai_core.rmq_default_config import DefaultConnectionParameters
from cgt_ai_core.rmq_consumer import RmqConsumer
from cgt_ai_core.rmq_producer import RmqProducer

LOGGER = logging.getLogger(__name__)


class Service:
    def __init__(self,
                 connection_params: ConnectionParameters = None,
                 host: str = None,
                 port: int = None,
                 username: str = None,
                 password: str = None):
        # connection_params provided
        if connection_params is not None:
            # any one of host/port/username/password provided with connection_params - throw an exception since this is prohibited
            if any(arg is not None for arg in (host, port, username, password)):
                raise ValueError('connection_params and host/port/username/password are mutually exclusive arguments. Please provide one or the other.')
            # no host/port/username/password provided - save connection_params since this is a valid configuration
            else:
                self.connection_params = connection_params
        # connection_params not provided
        else:
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

        self.consumers = []
        self.producers = []

        self.consumer_coroutines = []
        self.producer_coroutines = []

    def add_consumer(self, consumer : RmqConsumer):
        self.consumers.append(consumer)

    def add_producer(self, producer : RmqProducer):
        self.producers.append(producer)

    async def run(self):
        LOGGER.info('Running...')
        self.consumer_coroutines = [consumer.run() for consumer in self.consumers]
        self.producer_coroutines = [producer.run() for producer in self.producers]
        await asyncio.gather(*self.consumer_coroutines, *self.producer_coroutines)
