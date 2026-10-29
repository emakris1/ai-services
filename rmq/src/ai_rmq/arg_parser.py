import argparse

from ai_rmq.default_config import DefaultHost, DefaultPort, DefaultUsername, DefaultPassword


def add_rmq_connection_arguments(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    connection_group = parser.add_argument_group('RabbitMQ Server Connection Arguments')
    connection_group.add_argument('-i', '--rmq-host', default=DefaultHost,
                                  help='RabbitMQ server host')
    connection_group.add_argument('-p', '--rmq-port', type=int, default=DefaultPort,
                                  help='RabbitMQ server port')
    connection_group.add_argument('-u', '--rmq-username', default=DefaultUsername,
                                  help='RabbitMQ server username')
    connection_group.add_argument('-w', '--rmq-password', default=DefaultPassword,
                                  help='RabbitMQ server password')

    return parser
