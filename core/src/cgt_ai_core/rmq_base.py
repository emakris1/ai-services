import asyncio
import logging

from pika import ConnectionParameters
from pika.adapters.asyncio_connection import AsyncioConnection
from pika.channel import Channel
from pika.exchange_type import ExchangeType
from pika.frame import Method


LOGGER = logging.getLogger(__name__)


class RmqBase:
    def __init__(self,
                 connection_params: ConnectionParameters,
                 exchange_name: str,
                 exchange_type: ExchangeType,
                 queue_name: str = '',
                 routing_key: str = None):
        self.connection_params = connection_params
        self.exchange_name = exchange_name
        self.exchange_type = exchange_type
        self.queue_name = queue_name
        self.routing_key = routing_key if routing_key else queue_name

        self._connection = None
        self._channel = None

        self._closing = False

        self._run_should_stop_event = asyncio.Event()
        self._stop_completed_event = asyncio.Event()

    def open_connection(self):
        LOGGER.info(
            'Opening connection to %s:%s with credentials %s:%s...',
            self.connection_params.host,
            self.connection_params.port,
            self.connection_params.credentials.username,
            self.connection_params.credentials.password
        )

        self._connection = AsyncioConnection(
            parameters=self.connection_params,
            on_open_callback=self.on_connection_open,
            on_open_error_callback=self.on_connection_open_error,
            on_close_callback=self.on_connection_closed
        )

    def close_connection(self):
        LOGGER.info('Closing connection...')
        if self._connection:
            if self._connection.is_closing:
                LOGGER.info('Connection is already closing.')
            elif self._connection.is_closed:
                LOGGER.info('Connection is already closed')
            else:
                self._connection.close()
                LOGGER.info('Connection closed!')
        else:
            LOGGER.info('No connection to close.')

    def on_connection_open(self, _unused_connection: AsyncioConnection):
        LOGGER.info('Connection opened!')
        self.open_channel()

    def on_connection_open_error(self, _unused_connection: AsyncioConnection, ex: BaseException):
        LOGGER.exception('Connection failed to open.', exc_info=ex)
        self.stop()

    def on_connection_closed(self, _unused_connection: AsyncioConnection, ex: BaseException):
        if self._closing:
            LOGGER.info('Connection closed as part of shutdown: %s', ex)
            self._stop_completed_event.set() # Signal that stop() process is complete
        else:
            LOGGER.exception('Connection closed unexpectedly.', exc_info=ex)
            self.stop()

    def open_channel(self):
        LOGGER.info('Opening channel...')
        self._connection.channel(on_open_callback=self.on_channel_open)

    def close_channel(self):
        LOGGER.info('Closing channel...')
        if self._channel:
            if self._channel.is_open:
                self._channel.close()
            else:
                LOGGER.info('Channel is already closed.')
        else:
            LOGGER.info('Channel is not open.')

    def on_channel_open(self, channel: Channel):
        LOGGER.info('Channel opened!')
        self._channel = channel
        self._channel.add_on_close_callback(self.on_channel_closed)
        self.declare_exchange()

    def on_channel_closed(self, channel: Channel, ex: BaseException):
        LOGGER.exception('Channel %s was closed.', channel, exc_info=ex)
        self._channel = None

    def declare_exchange(self):
        LOGGER.info('Declaring exchange with name %s and type %s...', self.exchange_name, self.exchange_type)
        self._channel.exchange_declare(
            exchange=self.exchange_name,
            exchange_type=self.exchange_type,
            callback=self.on_exchange_declare_ok
        )

    def on_exchange_declare_ok(self, _unused_method_frame: Method):
        LOGGER.info('Exchange %s declared!', self.exchange_name)
        self.declare_queue()

    def declare_queue(self):
        LOGGER.info('Declaring queue %s...', self.queue_name if self.queue_name else 'anonymously')
        self._channel.queue_declare(queue=self.queue_name, callback=self.on_queue_declare_ok)

    def on_queue_declare_ok(self, method_frame: Method):
        assigned_queue_name = method_frame.method.queue
        LOGGER.info('Queue %s declared!', assigned_queue_name)
        # Update self.queue_name if it was assigned anonymously
        if not self.queue_name:
            self.queue_name = assigned_queue_name
        self.bind_queue()

    def bind_queue(self):
        LOGGER.info('Binding queue %s to exchange %s with routing key %s...',
                    self.queue_name, self.exchange_name, self.routing_key)
        self._channel.queue_bind(
            queue=self.queue_name,
            exchange=self.exchange_name,
            routing_key=self.routing_key,
            callback=self.on_queue_bind_ok
        )

    def on_queue_bind_ok(self, _unused_method_frame: Method):
        LOGGER.info('Queue %s successfully bound to exchange %s with routing key %s!',
                    self.queue_name, self.exchange_name, self.routing_key)
        self.post_queue_bind()

    def post_queue_bind(self):
        pass

    async def run(self):
        LOGGER.info('Running...')
        self._closing = False
        self._run_should_stop_event.clear()
        self._stop_completed_event.clear()

        try:
            self.pre_open_connection()
            self.open_connection()
            await self._run_should_stop_event.wait()
        except Exception as ex:
            LOGGER.exception('Unhandled exception', exc_info=ex)
            # Initiate a graceful shutdown attempt if run loop excepts
            if not self._closing:
                await self.stop()
        finally:
            LOGGER.info('Run completed.')

    async def stop(self):
        if self._closing and self._stop_completed_event.is_set():
            LOGGER.info('Already stopped.')
            return

        # Stop previously initiated, but not yet complete
        if self._closing:
            LOGGER.info('Stop already in progress. Waiting for completion...')
            await self._stop_completed_event.wait()
            LOGGER.info('Stop completed.')
            return

        # Stop initiated
        LOGGER.info('Stopping...')
        self._closing = True

        # Signal the run() method to exit its wait, regardless of how stop was initiated
        self._run_should_stop_event.set()
        # Clear the event for this stop sequence; it will be set by on_connection_closed
        self._stop_completed_event.clear()

        self.pre_close_connection()
        self.close_connection()

        LOGGER.info('Waiting for stop to complete...')
        await self._stop_completed_event.wait()
        LOGGER.info('Stop completed.')

    def pre_open_connection(self):
        pass

    def pre_close_connection(self):
        pass
