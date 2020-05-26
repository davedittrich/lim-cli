# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap

from cliff.lister import Lister
from lim.packet_cafe import add_packet_cafe_global_options
from lim.packet_cafe import get_results
from lim.packet_cafe import get_last_session_id
from lim.packet_cafe import get_last_request_id

logger = logging.getLogger(__name__)


def match(line=None, contains=[]):
    """
    Return true if line contains all of a set of
    specified strings between '/' characters.
    """
    if line is None:
        raise RuntimeError('[-] no line to search')
    if type(contains) is not list:
        raise RuntimeError('[-] kwarg "contains" must be a list')
    for s in contains:
        if not line.find(f'/{ s }/') >= 0:
            return False
    return True


class Results(Lister):
    """List all files produced by tools."""

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
        parser.epilog = textwrap.dedent("""
            List files produced as a result of processing uploaded files.

            You can filter results by session, by request, or by tool.
            Filtering matches lines that contain all of the specified values.

            To show results for a specific session or a specific request,
            provide them as arguments to the command.

            To show only results for a given tool, specify it with the
            ``-tool`` option.

            .. code-block:: console

                $ lim cafe admin results --tool networkml
                +---------------------------------------------------------------------------------------------------+
                | Results                                                                                           |
                +---------------------------------------------------------------------------------------------------+
                | /id/6f080abf-ef71-461d-b754-a81a54fb5ad5/d709256a73b44f4e82d45f6e4ffd03e5/networkml/metadata.json |
                | /id/86f71039-e6e5-44e2-90b4-3eaf27253d6d/fa142a055de24896923cc69407feeaba/networkml/metadata.json |
                | /id/278adaae-df30-4d7d-883a-990ddcf6ce88/a383d781275f4dbe9e2c78ec4b8abda4/networkml/metadata.json |
                | /id/bd976556-fbc3-4e2e-a808-7024c0c0f69b/6bb276459cba45b3abce9043d0bc0ad9/networkml/metadata.json |
                | /id/bd976556-fbc3-4e2e-a808-7024c0c0f69b/9e74cc6f818c47ea9cd8c8ab94ce93db/networkml/metadata.json |
                +---------------------------------------------------------------------------------------------------+

            ..

            See https://cyberreboot.gitbook.io/packet-cafe/design/api#v-1-id-results
            """)  # noqa
        return add_packet_cafe_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] listing results')
        columns = ['Results']
        data = []
        # Create a set of filters from args and options.
        contains = [
            item for item
            in [parsed_args.tool, parsed_args.sess_id, parsed_args.req_id]
            if item is not None
        ]
        # Only select items that match all filters
        data = [
            [row] for row in get_results()
            if match(line=row, contains=contains)
         ]
        return (columns, data)


# vim: set ts=4 sw=4 tw=0 et :
