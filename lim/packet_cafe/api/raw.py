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
from lim.packet_cafe import get_packet_cafe
from lim.packet_cafe import NO_SESSIONS_MSG
from pygments import formatters
from pygments import highlight
from pygments import lexers

logger = logging.getLogger(__name__)


class Raw(Command):
    """Get raw output from a specific tool, session, and request."""

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
            '-C', '--counter',
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

            See https://iqtlabs.gitbook.io/packet-cafe/design/api#api-v-1-raw-tool-counter-sess_id-req_id
            """)  # noqa
        return add_packet_cafe_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] get raw results')
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
                sess_id=parsed_args.sess_id,
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
        results = packet_cafe.get_raw(
            tool=tool,
            counter=parsed_args.counter,
            sess_id=sess_id,
            req_id=req_id
        )
        if results is not None:
            if parsed_args.pprint:
                # pp = pprint.PrettyPrinter(indent=parsed_args.indent)
                # pp.print(results)
                pp = pprint.PrettyPrinter()
                try:
                    pp.pprint(results)
                except BrokenPipeError:
                    pass
            else:
                if parsed_args.nocolor or not sys.stdout.isatty():
                    try:
                        print(json.dumps(results,
                                         indent=parsed_args.indent))
                    except BrokenPipeError:
                        pass
                else:
                    formatted_json = json.dumps(results,
                                                indent=parsed_args.indent)
                    colored_json = highlight(formatted_json,
                                             lexers.JsonLexer(),
                                             formatters.TerminalFormatter())
                    try:
                        print(colored_json)
                    except BrokenPipeError:
                        pass


# vim: set ts=4 sw=4 tw=0 et :
