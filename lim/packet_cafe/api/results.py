# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap

from cliff.command import Command
from lim.packet_cafe import _valid_counter
from lim.packet_cafe import add_packet_cafe_global_options
from lim.packet_cafe import choose_wisely
from lim.packet_cafe import get_packet_cafe
from lim.packet_cafe import NO_SESSIONS_MSG

logger = logging.getLogger(__name__)


class Results(Command):
    """Get the results from a tool for local storage or rendering."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument('sess_id', nargs='?', default=None)
        parser.add_argument('req_id', nargs='?', default=None)
        parser.add_argument(
            '-t', '--tool',
            metavar='<tool>',
            dest='tool',
            default=None,
            help='Only show results for specified tool (default: None)'
        )
        parser.add_argument(
            '-C', '--counter',
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

            See https://iqtlabs.gitbook.io/packet-cafe/design/api#api-v-1-results-tool-counter-sess_id-req_id
            """)  # noqa
        return add_packet_cafe_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] get tool output')
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
        tool = parsed_args.tool
        if tool is None:
            tools = packet_cafe.get_tools()
            tool = choose_wisely(
                from_list=tools,
                what="a tool",
                cancel_throws_exception=True
            )
        results = packet_cafe.get_worker_output(tool=tool,
                                                counter=parsed_args.counter,
                                                sess_id=sess_id,
                                                req_id=req_id)
        try:
            print(results)
        except BrokenPipeError:
            pass


# vim: set ts=4 sw=4 tw=0 et :
