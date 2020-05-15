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

            By default, basic status information is returned (including whether
            the call succeeded and the session ID + request ID for this request)
            and if the request was accepted, the progress of each worker is tracked
            in real time similar to the web UI.

            .. code-block:: console

                $ lim cafe upload test.pcap
                test.pcap success sess_id: 30b9ce67-75a4-49e6-b484-c4646b72fbd9 req_id: d38e7c1e0fc447d895716e2fa7d0b1af
                ncapture complete 2020-05-15T07:12:42.294824+00:00
                pcap-dot1q complete 2020-05-15T07:12:44.127325+00:00
                pcap-stats complete 2020-05-15T07:12:44.252338+00:00
                mercury complete 2020-05-15T07:12:45.693859+00:00
                snort complete 2020-05-15T07:12:49.101549+00:00
                pcap-splitter complete 2020-05-15T07:12:52.981766+00:00
                pcapplot complete 2020-05-15T07:13:22.872526+00:00
                networkml complete 2020-05-15T07:13:32.370534+00:00
                p0f complete 2020-05-15T07:13:46.141741+00:00

            ..

            If ``-v`` (or more) is given, even more information is produced and
            tracking is performed as well.

            If you do not wish to wait, use ``-q` for no output at all, or
            use ``--no-track`` to just get the status and IDs.  You can then get
            status using ``lim cafe status``:

            .. code-block:: console

                $ lim cafe upload test.pcap --no-track
                test.pcap success sess_id: 869d63d7-a46f-4221-8d59-610d9801e6a1 req_id: 79753a3b88af4f7e8a9e8462c2f9d50f
                $ lim cafe status
                +------------+-------------+----------------------------------+
                | Tool       | State       | Timestamp                        |
                +------------+-------------+----------------------------------+
                | snort      | In progress | 2020-05-15T07:18:55.281469+00:00 |
                | mercury    | In progress | 2020-05-15T07:18:56.288996+00:00 |
                | ncapture   | Complete    | 2020-05-15T07:18:56.881295+00:00 |
                | pcap-dot1q | In progress | 2020-05-15T07:18:56.880669+00:00 |
                | pcap-stats | In progress | 2020-05-15T07:18:56.923709+00:00 |
                +------------+-------------+----------------------------------+
                $ lim cafe status
                +---------------+-------------+----------------------------------+
                | Tool          | State       | Timestamp                        |
                +---------------+-------------+----------------------------------+
                | snort         | Complete    | 2020-05-15T07:19:02.913388+00:00 |
                | networkml     | In progress | 2020-05-15T07:19:07.484375+00:00 |
                | pcap-splitter | Complete    | 2020-05-15T07:19:07.994744+00:00 |
                | mercury       | Complete    | 2020-05-15T07:19:00.197828+00:00 |
                | pcap-dot1q    | Complete    | 2020-05-15T07:18:59.070603+00:00 |
                | ncapture      | Complete    | 2020-05-15T07:18:56.881295+00:00 |
                | pcapplot      | In progress | 2020-05-15T07:19:07.046718+00:00 |
                | pcap-stats    | Complete    | 2020-05-15T07:18:59.209291+00:00 |
                | p0f           | In progress | 2020-05-15T07:19:07.994061+00:00 |
                +---------------+-------------+----------------------------------+

            ..

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
