# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap

from cliff.command import Command
from lim.packet_cafe import add_packet_cafe_global_options
from lim.packet_cafe import get_packet_cafe
from lim.packet_cafe import NO_SESSIONS_MSG

logger = logging.getLogger(__name__)


class Stop(Command):
    """Stop jobs of a request ID."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument('sess_id', nargs='?', default=None)
        parser.add_argument('req_id', nargs='?', default=None)
        parser.epilog = textwrap.dedent("""
            Stop jobs of a request ID.

            This is a placeholder for future functionality.
            See https://iqtlabs.gitbook.io/packet-cafe/design/api#api-v-1-stop-sess_id-req_id
            """)  # noqa
        return add_packet_cafe_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] stopping jobs for request')
        packet_cafe = get_packet_cafe(self.app, parsed_args)
        ids = packet_cafe.get_session_ids()
        if not len(ids):
            raise RuntimeError(NO_SESSIONS_MSG)
        sess_id = packet_cafe.get_session_id(
                sess_id=parsed_args.sess_id,
                choose=parsed_args.choose)
        if sess_id not in ids:
            raise RuntimeError(
                f'[-] session ID { sess_id } not found')
        req_id = packet_cafe.get_request_id(
                req_id=parsed_args.req_id,
                choose=parsed_args.choose)
        status = packet_cafe.stop(sess_id=sess_id, req_id=req_id)
        if status is None:
            raise RuntimeError('[-] failed to stop '
                               f'session { sess_id }, '
                               f'request { req_id }')


# vim: set ts=4 sw=4 tw=0 et :
