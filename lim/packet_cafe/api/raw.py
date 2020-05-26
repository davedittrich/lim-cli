# -*- coding: utf-8 -*-

import argparse
import json
import logging
import pprint
import sys
import textwrap

from cliff.command import Command
from lim.packet_cafe import add_packet_cafe_global_options
from lim.packet_cafe import _valid_counter
from lim.packet_cafe import choose_wisely
from lim.packet_cafe import get_request_ids
from lim.packet_cafe import get_session_ids
from lim.packet_cafe import get_tools
from lim.packet_cafe import get_raw
from lim.packet_cafe import get_last_session_id
from lim.packet_cafe import get_last_request_id
from lim.packet_cafe import check_remind_defaulting
from pygments import formatters
from pygments import highlight
from pygments import lexers

logger = logging.getLogger(__name__)


class Raw(Command):
    """Get raw output from a specific tool, session, and request."""

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
            '-P', '--pprint',
            action='store_true',
            dest='pprint',
            default=False,
            help='Print with pprint module (default: False)'
        )
        parser.add_argument(
            '-I', '--indent',
            type=_valid_counter,
            dest='indent',
            default=2,
            help=('Indentation amount in characters (default: 2)')
        )
        parser.add_argument(
            '--no-color',
            action='store_true',
            dest='nocolor',
            default=False,
            help='Print without terminal coloring (default: False)'
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
            Get raw output from a specific tool, session, and request.

            To select the tool from which you want output, use the ``--tool`` option.
            You must select a tool (from the list produced by ``lim cafe tools``.)

            .. code-block:: console

                $ lim cafe raw --tool networkml | head
                [
                  {
                    "81778bb8a9b946ba82659732baacdb44": {
                      "valid": true,
                      "pcap_labels": "ip-147-32-84-79-147-32-84-165-147-32-84-79-data-udp-frame-eth-ip-port-0",
                      "decisions": {
                        "behavior": "normal",
                        "investigate": false
                      },
                      "classification": {

            ..

            If there is more than one file, use ``--counter`` to select which one.

            By default, JSON output is colored unless ``stdout`` is not a TTY (e.g.,
            when piping output to another program, or redirecting output to a file.)
            Disable colored output with ``--no-color``, select ``pprint`` style
            pretty-printing with ``--pprint``, and control indentation with
            ``--indent``.

            See https://cyberreboot.gitbook.io/packet-cafe/design/api#api-v-1-raw-tool-counter-sess_id-req_id
            """)  # noqa
        return add_packet_cafe_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] get raw results')
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
        results = get_raw(tool=tool,
                          counter=parsed_args.counter,
                          sess_id=sess_id,
                          req_id=req_id)
        if results is not None:
            if parsed_args.pprint:
                # pp = pprint.PrettyPrinter(indent=parsed_args.indent)
                # pp.print(results)
                pp = pprint.PrettyPrinter()
                pp.pprint(results)
            else:
                if parsed_args.nocolor or not sys.stdout.isatty():
                    print(json.dumps(results, indent=parsed_args.indent))
                else:
                    formatted_json = json.dumps(results,
                                                indent=parsed_args.indent)
                    colored_json = highlight(formatted_json,
                                             lexers.JsonLexer(),
                                             formatters.TerminalFormatter())
                    print(colored_json)


# vim: set ts=4 sw=4 tw=0 et :
