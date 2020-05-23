# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap

from cliff.lister import Lister
from lim.packet_cafe import add_packet_cafe_global_options
from lim.packet_cafe import get_session_ids

logger = logging.getLogger(__name__)


class Sessions(Lister):
    """List session IDs in packet-cafe service."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.epilog = textwrap.dedent("""
            List the current session IDS in the packet-cafe service.

            .. code-block:: console

                $ lim cafe admin sessions
                +--------------------------------------+
                | SessionId                            |
                +--------------------------------------+
                | 57b1484b-5502-4e3c-b6bc-854d4aeb2038 |
                | 57be4843-32c0-4943-93d8-d1ec9bc0e792 |
                | 2d222a53-5b01-4d5e-a659-7da7c21d3cf6 |
                | 73d532d7-3b2b-4a93-9a68-ae7091af6a2f |
                | 9a949fe6-6520-437f-89ec-e7af6925b1e0 |
                | 7eedfd93-4f65-4422-8d70-a4edf47d7364 |
                | a42ee6ab-d60b-4d8e-a1df-cb3dc6985c81 |
                +--------------------------------------+

            ..

            See https://cyberreboot.gitbook.io/packet-cafe/design/api#v-1-ids
            """)
        return add_packet_cafe_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] listing session ids')
        columns = ['SessionId']
        data = [[row] for row in get_session_ids()]
        if not bool(len(data)):
            logger.info('[-] packet-cafe server has no sessions')
        return (columns, data)


# vim: set ts=4 sw=4 tw=0 et :
