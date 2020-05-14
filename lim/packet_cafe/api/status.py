# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap

from cliff.lister import Lister
from lim.packet_cafe import add_packet_cafe_global_options
from lim.packet_cafe import chose_wisely
from lim.packet_cafe import get_request_ids
from lim.packet_cafe import get_session_ids
from lim.packet_cafe import get_status

logger = logging.getLogger(__name__)


class Status(Lister):
    """Return the status of all tools for a session and request ID."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument('sess_id', nargs='?', default=None)
        parser.add_argument('req_id', nargs='?', default=None)
        parser.epilog = textwrap.dedent("""
            Return the status of all tools for a session and request ID.

            See https://cyberreboot.gitbook.io/packet-cafe/design/api#api-v-1-status-sess_id-req_id
            """)  # noqa
        return add_packet_cafe_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] showing status for request')
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
        columns = ['Tool', 'State', 'Timestamp']
        data = list()
        status = get_status(sess_id=sess_id, req_id=req_id)
        if status is None:
            raise RuntimeError(f'failed to get status for '
                               f'session { sess_id }, '
                               f'request { req_id }')
        for k, v in status.items():
            if type(v) is dict:
                data.append((k, v['state'], v['timestamp']))
        return (columns, data)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
