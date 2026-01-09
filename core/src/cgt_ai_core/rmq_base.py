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
                 routing_key: str = ''):
        self.connection_params = connection_params
        self.exchange_name = exchange_name
        self.exchange_type = exchange_type
        self.routing_key = routing_key

        self.connection = None
        self.channel = None

        self.closing = False

        self.run_should_stop_event = asyncio.Event()
        self.stop_completed_event = asyncio.Event()

    def pre_open_connection(self):
        pass

    def open_connection(self):
        LOGGER.debug(
            'Opening connection to %s:%s with credentials %s:%s...',
            self.connection_params.host,
            self.connection_params.port,
            self.connection_params.credentials.username,
            self.connection_params.credentials.password
        )

        if self.connection and self.connection.is_open:
            LOGGER.debug('Connection is already open.')
            return

        self.pre_open_connection()

        self.connection = AsyncioConnection(
            parameters=self.connection_params,
            on_open_callback=self.on_connection_open,
            on_open_error_callback=self.on_connection_open_error,
            on_close_callback=self.on_connection_closed
        )

    def pre_close_connection(self):
        pass

    def close_connection(self):
        LOGGER.debug('Closing connection...')
        if self.connection:
            if self.connection.is_closing:
                LOGGER.debug('Connection is already closing.')
            elif self.connection.is_closed:
                LOGGER.debug('Connection is already closed.')
            else:
                self.pre_close_connection()
                self.connection.close()
                LOGGER.debug('Connection closed.')
        else:
            LOGGER.debug('No connection to close.')

    def on_connection_open(self, _unused_connection: AsyncioConnection):
        LOGGER.debug('Connection opened!')
        self.open_channel()

    def on_connection_open_error(self, _unused_connection: AsyncioConnection, ex: BaseException):
        LOGGER.exception('Connection failed to open.', exc_info=ex)
        self.stop()

    def on_connection_closed(self, _unused_connection: AsyncioConnection, ex: BaseException):
        if self.closing:
            LOGGER.debug('Connection closed as part of shutdown.')
            self.stop_completed_event.set() # Signal that stop() process is complete
        else:
            LOGGER.exception('Connection closed unexpectedly.', exc_info=ex)
            self.stop()

    def open_channel(self):
        LOGGER.debug('Opening channel...')
        self.connection.channel(on_open_callback=self.on_channel_open)

    def close_channel(self):
        LOGGER.debug('Closing channel...')
        if self.channel:
            if self.channel.is_open:
                self.channel.close()
            else:
                LOGGER.debug('Channel is already closed.')
        else:
            LOGGER.debug('Channel is not open.')

    def on_channel_open(self, channel: Channel):
        LOGGER.debug('Channel %s opened!', channel.channel_number)
        self.channel = channel
        self.channel.add_on_close_callback(self.on_channel_closed)
        self.declare_exchange()

    def on_channel_closed(self, channel: Channel, ex: BaseException):
        LOGGER.exception('Channel %s was closed.', channel, exc_info=ex)
        self.channel = None

    def declare_exchange(self):
        LOGGER.debug('Declaring exchange with name "%s" and type "%s"...', self.exchange_name, self.exchange_type)
        self.channel.exchange_declare(
            exchange=self.exchange_name,
            exchange_type=self.exchange_type,
            callback=self.on_exchange_declare_ok
        )

    def on_exchange_declare_ok(self, _unused_method_frame: Method):
        LOGGER.debug('Exchange "%s" declared!', self.exchange_name)
        self.post_exchange_declare()

    def post_exchange_declare(self):
        pass

    async def run(self):
        LOGGER.info('Running...')
        self.closing = False
        self.run_should_stop_event.clear()
        self.stop_completed_event.clear()

        self.open_connection()

        try:
            # Run until a stop event is received or the run loop excepts
            await self.run_should_stop_event.wait()
        except asyncio.CancelledError as exc:
            LOGGER.exception('Run cancelled', exc_info=exc)
        except Exception as exc:
            LOGGER.exception('Unhandled exception', exc_info=exc)
        finally:
            if not self.closing:
                await self.stop()

    async def stop(self):
        if self.closing and self.stop_completed_event.is_set():
            LOGGER.info('Already stopped.')
            return

        # Stop previously initiated, but not yet complete
        if self.closing:
            LOGGER.info('Stop already in progress. Waiting for completion...')

            try:
                await self.stop_completed_event.wait()
            except asyncio.CancelledError as exc:
                LOGGER.exception('Stop cancelled.', exc_info=exc)
            except Exception as exc:
                LOGGER.exception('Unhandled exception.', exc_info=exc)

            LOGGER.info('Stop completed.')
            return

        # Stop initiated
        LOGGER.info('Stopping...')
        self.closing = True

        # Signal the run() method to exit its wait, regardless of how stop was initiated
        self.run_should_stop_event.set()
        # Clear the event for this stop sequence; it will be set by on_connection_closed
        self.stop_completed_event.clear()

        self.close_connection()

        LOGGER.info('Waiting for stop to complete...')

        try:
            await self.stop_completed_event.wait()
        except asyncio.CancelledError as exc:
            LOGGER.exception('Stop cancelled.', exc_info=exc)
        except Exception as exc:
            LOGGER.exception('Unhandled exception.', exc_info=exc)

        LOGGER.info('Stop completed.')
