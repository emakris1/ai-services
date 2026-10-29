import argparse
import logging

from ai_core.rmq_default_config import DefaultHost, DefaultPort, DefaultUsername, DefaultPassword


def get_service_arg_parser(description: str):
    parser = argparse.ArgumentParser(description=description)

    connection_group = parser.add_argument_group('RabbitMQ Server Connection Arguments')
    connection_group.add_argument('-i', '--rmq-host', default=DefaultHost,
                                  help='RabbitMQ server host')
    connection_group.add_argument('-p', '--rmq-port', type=int, default=DefaultPort,
                                  help='RabbitMQ server port')
    connection_group.add_argument('-u', '--rmq-username', default=DefaultUsername,
                                  help='RabbitMQ server username')
    connection_group.add_argument('-w', '--rmq-password', default=DefaultPassword,
                                  help='RabbitMQ server password')

    logging_group = parser.add_argument_group('Logging Arguments')
    logging_group.add_argument('-l', '--log-level', default='INFO',
                               choices=logging.getLevelNamesMapping().keys(), help='Logging level')

    return parser
