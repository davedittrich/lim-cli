# -*- coding: utf-8 -*-

import argparse
import logging
import os
import textwrap

from cliff.command import Command
from lim.packet_cafe import add_packet_cafe_global_options
from lim.packet_cafe import track_progress
from lim.packet_cafe import upload
from lim.packet_cafe import get_last_session_id


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
            '--no-track',
            action='store_true',
            dest='no_track',
            default=False,
            help="Do not track worker status in real time (default: False)"
        )
        parser.add_argument(
            'pcap',
            nargs=1,
            default=None,
            help="PCAP file to upload"
        )
        parser.epilog = textwrap.dedent("""
            Upload a file to the packet-cafe service for processing.

            You can attempt to re-use the last session ID by using
            ``--session-id last``.  If that session does not exist, a new
            session ID will be generated.

            See https://cyberreboot.gitbook.io/packet-cafe/design/api#api-v-1-upload
            """)  # noqa
        return add_packet_cafe_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] upload file')
        # Avoid the confusing double-negative if statement
        track_status = (self.app.options.verbose_level > 0
                        and parsed_args.no_track is not False)
        fname = parsed_args.pcap[0]
        if parsed_args.sessionId == "last":
            parsed_args.sessionId = get_last_session_id()
        if not os.path.exists(fname):
            raise RuntimeError(f'file { fname } not found')
        result = upload(fname=fname, sessionId=parsed_args.sessionId)
        if self.app.options.verbose_level > 0:
            # NOTE(dittrich): Don't forget: 'req_id' is 'uuid' in result
            readable_result = (f"{ result['filename'] } "
                               f"{ result['status'].lower() } "
                               f"sess_id: { result['sess_id'] } "
                               f"req_id: { result['uuid'] }")
            logger.info(readable_result)
        if track_status:
            track_progress(sess_id=result['sess_id'],
                           req_id=result['uuid'],
                           debug=self.app.options.debug)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
