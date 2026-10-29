import logging

from pika import ConnectionParameters
from pika.adapters.asyncio_connection import AsyncioConnection
from pika.channel import Channel
from pika.credentials import PlainCredentials
from typing import Callable

from ai_rmq.default_config import DefaultConnectionParameters

LOGGER = logging.getLogger(__name__)

class RmqConnection:
    def __init__(
        self,
        host: str = None,
        port: int = None,
        username: str = None,
        password: str = None,
        on_connection_opened_callback: Callable[[], None] = lambda: None,
        on_connection_closed_callback: Callable[[], None] = lambda: None,
        on_channel_opened_callback: Callable[[], None] = lambda: None,
        on_channel_closed_callback: Callable[[], None] = lambda: None,
    ):
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

        self.on_connection_opened_callback: Callable[[], None] = on_connection_opened_callback
        self.on_connection_closed_callback: Callable[[], None] = on_connection_closed_callback
        self.on_channel_opened_callback: Callable[[], None] = on_channel_opened_callback
        self.on_channel_closed_callback: Callable[[], None] = on_channel_closed_callback

        self.connection: AsyncioConnection | None = None
        self.channel: Channel | None = None

        self.closing: bool = False

    def open_connection(self) -> None:
        LOGGER.info('Opening connection...')
        LOGGER.debug(
            'Connecting to %s:%s with credentials %s:%s...',
            self.connection_params.host,
            self.connection_params.port,
            self.connection_params.credentials.username,
            self.connection_params.credentials.password
        )

        if self.connection and self.connection.is_open:
            LOGGER.info('Connection is already open.')
            return

        self.connection = AsyncioConnection(
            parameters=self.connection_params,
            on_open_callback=self.on_connection_opened,
            on_open_error_callback=self.on_connection_open_error,
            on_close_callback=self.on_connection_closed
        )

    def close_connection(self) -> None:
        LOGGER.info('Closing connection...')
        if self.connection:
            if self.connection.is_closing or self.closing:
                LOGGER.info('Connection is already closing.')
            elif self.connection.is_closed:
                LOGGER.info('Connection is already closed.')
            else:
                self.closing = True
                self.close_channel()
                self.connection.close()
        else:
            LOGGER.info('Connection is already closed, or was never opened.')

    def on_connection_opened(self, _unused_connection: AsyncioConnection) -> None:
        LOGGER.debug('Connection opened!')
        self.on_connection_opened_callback()
        self.open_channel()

    def on_connection_open_error(self, _unused_connection: AsyncioConnection, ex: BaseException) -> None:
        LOGGER.exception('Connection failed to open.', exc_info=ex)
        self.connection = None

    def on_connection_closed(self, _unused_connection: AsyncioConnection, ex: BaseException) -> None:
        if self.closing:
            LOGGER.debug('Connection closed as part of shutdown.')
        else:
            LOGGER.exception('Connection closed unexpectedly.', exc_info=ex)
        self.connection = None
        self.closing = False
        self.on_connection_closed_callback()

    def open_channel(self) -> None:
        LOGGER.debug('Opening channel...')
        if self.channel:
            if self.channel.is_opening:
                LOGGER.debug('Channel is already opening.')
            elif self.channel.is_open:
                LOGGER.debug('Channel is already open.')
            else:
                self.connection.channel(on_open_callback=self.on_channel_opened)
        else:
            self.connection.channel(on_open_callback=self.on_channel_opened)

    def close_channel(self) -> None:
        LOGGER.debug('Closing channel...')
        if self.channel:
            if self.channel.is_closing or self.closing:
                LOGGER.debug('Channel is already closing.')
            elif self.channel.is_closed:
                LOGGER.debug('Channel is already closed.')
            else:
                self.channel.close()
        else:
            LOGGER.debug('Channel was never opened. Nothing to close.')

    def on_channel_opened(self, channel: Channel) -> None:
        LOGGER.debug('Channel #%d opened!', channel.channel_number)
        self.channel = channel
        self.channel.add_on_close_callback(self.on_channel_closed)
        self.on_channel_opened_callback()

    def on_channel_closed(self, channel: Channel, ex: BaseException) -> None:
        if self.closing:
            LOGGER.debug('Channel #%d closed as part of shutdown.', channel.channel_number)
        else:
            LOGGER.exception('Channel #%d closed unexpectedly.', channel.channel_number, exc_info=ex)
        self.channel = None
        self.on_channel_closed_callback()
