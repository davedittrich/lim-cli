# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap

from cliff.lister import Lister
from lim.packet_cafe import get_results

logger = logging.getLogger(__name__)


class Results(Lister):
    """List all files produced by tools."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.epilog = textwrap.dedent("""
            List all files produced as a result of processing uploaded files.

            See https://cyberreboot.gitbook.io/packet-cafe/design/api#v-1-id-results
            """)  # noqa
        return parser

    def take_action(self, parsed_args):
        logger.debug('[+] listing results')
        columns = ['Results']
        data = [[row] for row in get_results()]
        return (columns, data)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
