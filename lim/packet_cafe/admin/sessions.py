# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap

from cliff.lister import Lister
from lim.packet_cafe import get_session_ids

logger = logging.getLogger(__name__)


class Sessions(Lister):
    """List session IDs in packet-cafe service."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.epilog = textwrap.dedent("""
            List the current session IDS in the packet-cafe service.

            See https://cyberreboot.gitbook.io/packet-cafe/design/api#v-1-ids
            """)
        return parser

    def take_action(self, parsed_args):
        logger.debug('[+] listing session ids')
        columns = ['SessionId']
        data = [[row] for row in get_session_ids()]
        return (columns, data)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
