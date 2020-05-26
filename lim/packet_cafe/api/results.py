# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap

from cliff.command import Command
from lim.packet_cafe import _valid_counter
from lim.packet_cafe import add_packet_cafe_global_options
from lim.packet_cafe import check_remind_defaulting
from lim.packet_cafe import choose_wisely
from lim.packet_cafe import get_request_ids
from lim.packet_cafe import get_session_ids
from lim.packet_cafe import get_tools
from lim.packet_cafe import get_worker_output
from lim.packet_cafe import get_last_session_id
from lim.packet_cafe import get_last_request_id

logger = logging.getLogger(__name__)


class Results(Command):
    """Get the results from a tool for local storage or rendering."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            'sess_id', nargs='?', default=get_last_session_id())
        parser.add_argument(
            'req_id', nargs='?', default=get_last_request_id())
        parser.add_argument(
            '-t', '--tool',
            metavar='<tool>',
            dest='tool',
            default=None,
            help='Only show results for specified tool (default: None)'
        )
        parser.add_argument(
            '-c', '--counter',
            metavar='<counter>',
            type=_valid_counter,
            dest='counter',
            default=1,
            help=('Counter for selecting a specific file '
                  'from a set (default: 1)')
        )
        parser.epilog = textwrap.dedent("""
            Get the results from a tool (in the form of HTML) for local storage
            or rendering.

            In this version, the contents are simply put on ``stdout`` and you must
            redirect them to a file. (In future, this will be saved and a browser
            opened to view the file, as if you had selected a result in the web UI.)

            See https://cyberreboot.gitbook.io/packet-cafe/design/api#api-v-1-results-tool-counter-sess_id-req_id
            """)  # noqa
        return add_packet_cafe_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] get tool output')
        ids = get_session_ids()
        if parsed_args.sess_id is not None and not parsed_args.choose:
            sess_id = check_remind_defaulting(
                parsed_args.sess_id, 'last session id')
        else:
            sess_id = choose_wisely(
                from_list=ids,
                what="session",
                cancel_throws_exception=True
            )
        if sess_id not in ids:
            raise RuntimeError(f'[-] session ID { sess_id } not found')
        if parsed_args.req_id is not None and not parsed_args.choose:
            req_id = check_remind_defaulting(
                parsed_args.req_id, 'last request id')
        else:
            req_id = choose_wisely(
                from_list=get_request_ids(sess_id=sess_id),
                what="a request",
                cancel_throws_exception=True
            )
        tool = parsed_args.tool
        if tool is None:
            tools = get_tools()
            tool = choose_wisely(
                from_list=tools,
                what="a tool",
                cancel_throws_exception=True
            )
        results = get_worker_output(tool=tool,
                                    counter=parsed_args.counter,
                                    sess_id=sess_id,
                                    req_id=req_id)
        print(results)


# vim: set ts=4 sw=4 tw=0 et :
