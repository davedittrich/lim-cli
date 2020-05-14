# -*- coding: utf-8 -*-

import argparse
import logging
import os
import textwrap

from cliff.command import Command
from lim.packet_cafe import add_packet_cafe_global_options
from lim.packet_cafe import upload

logger = logging.getLogger(__name__)


class Upload(Command):
    """Upload a file to the packet-cafe service for processing."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '--session-id',
            metavar='<uuid>',
            dest='sessionId',
            default=None,
            help='Session ID (default: generate at runtime)'
        )
        parser.add_argument(
            'pcap',
            nargs=1,
            default=None,
            help="PCAP file to upload"
        )
        parser.epilog = textwrap.dedent("""
            Upload a file to the packet-cafe service for processing.

            See https://cyberreboot.gitbook.io/packet-cafe/design/api#api-v-1-upload
            """)  # noqa
        return add_packet_cafe_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] upload file')
        fname = parsed_args.pcap[0]
        if not os.path.exists(fname):
            raise RuntimeError(f'file { fname } not found')
        result = upload(fname=fname, sessionId=parsed_args.sessionId)
        if result is not None:
            logger.info(result)

# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
