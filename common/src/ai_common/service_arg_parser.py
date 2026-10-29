import argparse
import logging

from ai_rmq.arg_parser import add_rmq_connection_arguments


def get_service_arg_parser(description: str):
    parser = argparse.ArgumentParser(description=description)

    add_rmq_connection_arguments(parser)

    logging_group = parser.add_argument_group('Logging Arguments')
    logging_group.add_argument('-l', '--log-level', default='INFO',
                               choices=logging.getLevelNamesMapping().keys(), help='Logging level')

    return parser
