# -*- coding: utf-8 -*-

import argparse
import logging
import sys
import textwrap

from cliff.lister import Lister
from lim.packet_cafe import add_packet_cafe_global_options
from lim.packet_cafe import get_packet_cafe
from lim.packet_cafe import NO_SESSIONS_MSG

logger = logging.getLogger(__name__)


class Sessions(Lister):
    """List session IDs in packet-cafe service."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.epilog = textwrap.dedent("""
            List the current session IDS in the packet-cafe service.
            Returns shell exit code ``0`` if one or more sessiona are
            present, or ``1`` if none are present.

            Use the ``-q`` option to suppress the output table or error
            message.

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

            See https://iqtlabs.gitbook.io/packet-cafe/design/api#v-1-ids
            """)
        return add_packet_cafe_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] listing session ids')
        packet_cafe = get_packet_cafe(self.app, parsed_args)
        columns = ['SessionId']
        data = [[row] for row in packet_cafe.get_session_ids()]
        if not bool(len(data)):
            if bool(self.app_args.verbose_level):
                logger.info(NO_SESSIONS_MSG)
            sys.exit(1)
        if not bool(self.app_args.verbose_level):
            sys.exit(0)
        return (columns, data)


# vim: set ts=4 sw=4 tw=0 et :
