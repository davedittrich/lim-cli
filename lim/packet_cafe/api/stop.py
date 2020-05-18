# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap

from cliff.command import Command
from lim.packet_cafe import add_packet_cafe_global_options
from lim.packet_cafe import chose_wisely
from lim.packet_cafe import get_request_ids
from lim.packet_cafe import get_session_ids
from lim.packet_cafe import get_last_session_id
from lim.packet_cafe import get_last_request_id
from lim.packet_cafe import stop

logger = logging.getLogger(__name__)


class Stop(Command):
    """Stop jobs of a request ID."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            'sess_id', nargs='?', default=get_last_session_id())
        parser.add_argument(
            'req_id', nargs='?', default=get_last_request_id())
        parser.epilog = textwrap.dedent("""
            Stop jobs of a request ID.

            This is a placeholder for future functionality.
            See https://cyberreboot.gitbook.io/packet-cafe/design/api#api-v-1-stop-sess_id-req_id
            """)  # noqa
        return add_packet_cafe_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] stopping jobs for request')
        ids = get_session_ids()
        if parsed_args.sess_id is not None:
            sess_id = parsed_args.sess_id
        else:
            sess_id = chose_wisely(from_list=ids,
                                   what="a session",
                                   cancel_throws_exception=True)
        if sess_id not in ids:
            raise RuntimeError(f'Session ID { sess_id } not found')
        if parsed_args.req_id is not None:
            req_id = parsed_args.req_id
        else:
            req_id = chose_wisely(
                from_list=get_request_ids(sess_id=sess_id),
                what="a request",
                cancel_throws_exception=True
            )
        status = stop(sess_id=sess_id, req_id=req_id)
        if status is None:
            raise RuntimeError('failed to stop '
                               f'session { sess_id }, '
                               f'request { req_id }')


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :