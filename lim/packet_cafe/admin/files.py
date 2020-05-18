# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap

from cliff.lister import Lister
from lim.packet_cafe import add_packet_cafe_global_options
from lim.packet_cafe import get_files

logger = logging.getLogger(__name__)


class Files(Lister):
    """List files in packet-cafe server."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.epilog = textwrap.dedent("""
            Lists all files uploaded into the packet-cafe server.  This can produce
            a large amount of output with very long lines, so you may want to use the
            ``--fit-width`` option to break lines to fit the screen.

            See https://cyberreboot.gitbook.io/packet-cafe/design/api#v-1-id-files
            """)  # noqa
        return add_packet_cafe_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] listing files')
        columns = ['File']
        data = [[row] for row in get_files()]
        return (columns, data)


# vim: set ts=4 sw=4 tw=0 et :
