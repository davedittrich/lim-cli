# -*- coding: utf-8 -*-

import argparse
import logging
import os
import textwrap

from cliff.command import Command
from lim.packet_cafe import add_packet_cafe_global_options
from lim.packet_cafe import get_packet_cafe


logger = logging.getLogger(__name__)


class Upload(Command):
    """Upload a file to the packet-cafe service for processing."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '--no-track',
            action='store_true',
            dest='no_track',
            default=False,
            help='Do not track worker status in real time (default: False)'
        )
        parser.add_argument(
            '--wait',
            action='store_true',
            dest='wait',
            default=False,
            help="Wait for processing to finish (default: False)"
        )
        parser.add_argument(
            'pcap',
            nargs=1,
            default=None,
            help='Path to PCAP file to upload'
        )
        session = parser.add_mutually_exclusive_group(required=False)
        session.add_argument(
            'sess_id',
            nargs='?',
            default=None,
            help='Optional session ID (default is to generate)'
        )
        session.add_argument(
            '--reuse-session',
            action='store_true',
            dest='reuse_session',
            default=False,
            help='Reuse the last session ID (default: False)'
        )
        parser.epilog = textwrap.dedent("""
            Upload a file to the packet-cafe service for processing.

            By default, the file is added to a new session. To instead
            add this file to an existing session, you can (a) specify the
            session ID as an argument on the command line, (b) add the
            ``--choose`` flag to interactively select the session ID from
            existing sessions, (c) add the ``--reuse-session`` flag to
            associate this file with the last session ID, or allow the
            default behavior of generating a new session.

            By default, basic status information is returned (including whether
            the call succeeded and the session ID + request ID for this request)
            and if the request was accepted, the progress of each worker is tracked
            in real time similar to the web UI.

            .. code-block:: console

                $ lim cafe upload ~/git/packet_cafe/notebooks/smallFlows.pcap
                [+] Upload smallFlows.pcap: success
                [+] Session ID (sess_id): 30b9ce67-75a4-49e6-b484-c4646b72fbd9
                [+] Request ID (req_id): 4e058115ed19491193eadf58f105032b
                [+] pcap-stats:    complete 2020-05-23T17:29:56.982084+00:00
                [+] pcap-dot1q:    complete 2020-05-23T17:29:55.773211+00:00
                [+] ncapture:      complete 2020-05-23T17:29:53.333307+00:00
                [+] mercury:       complete 2020-05-23T17:29:59.330288+00:00
                [+] snort:         complete 2020-05-23T17:30:02.781840+00:00
                [+] pcap-splitter: complete 2020-05-23T17:31:10.060056+00:00
                [+] networkml:     complete 2020-05-23T17:32:13.648982+00:00
                [+] p0f:           complete 2020-05-23T17:32:21.438466+00:00
                [+] pcapplot:      complete 2020-05-23T17:33:05.999342+00:00

            ..

            If ``-v`` (or more) is given, even more information is produced and
            tracking is performed as well.

            Adding the ``--elapsed`` option includes elapsed lap time (per worker)
            and total time for all workers.

            .. code-block:: console

                $ lim cafe upload CTU-Malware-Capture-Botnet-114-1/2015-04-09_capture-win2.pcap --elapsed
                [+] Upload 2015-04-09_capture-win2.pcap: success
                [+] Session ID (sess_id): 46d4f9a9-d5db-487e-a261-91764c044b44
                [+] Request ID (req_id): a93591b554fe420ebbcf14b67fc8d298
                [+] ncapture:      complete 2020-05-27T03:26:53.894222+00:00 (00:00:05.07)
                [+] pcap-stats:    complete 2020-05-27T03:26:56.531330+00:00 (00:00:05.07)
                [+] pcap-dot1q:    complete 2020-05-27T03:26:56.311676+00:00 (00:00:05.07)
                [+] mercury:       complete 2020-05-27T03:26:59.670225+00:00 (00:00:07.10)
                [+] snort:         complete 2020-05-27T03:27:03.241917+00:00 (00:00:11.16)
                [+] pcap-splitter: complete 2020-05-27T03:27:03.122224+00:00 (00:00:11.16)
                [+] p0f:           complete 2020-05-27T03:27:07.341062+00:00 (00:00:15.22)
                [+] networkml:     complete 2020-05-27T03:27:08.732745+00:00 (00:00:17.25)
                [+] pcapplot:      complete 2020-05-27T03:27:10.634384+00:00 (00:00:19.27)
                [+] Elapsed time 00:00:22.86

            ..

            Adding the ``--no-track`` option will return the upload status and both
            session and request IDs.  You can then check on the status as needed
            using ``lim cafe status``:

            .. code-block:: console

                $ lim cafe upload test.pcap --no-track
                [+] Upload test.pcap: success
                [+] Session ID (sess_id): d7c9eaaa-6360-44d0-b821-097b17d1b4fb
                [+] Request ID (req_id): 20c34e04b91a4fed9b4f876e67a218c9
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

            Using the ``-q`` flag will no produce any output and will also return
            immediately without tracking processing.  In circumstances where you are
            performing lots of uploads, it may be better to wait until all processing
            for each file is done is done before uploading the next file.  Use the
            ``--wait`` flag to do this.

            See https://iqtlabs.gitbook.io/packet-cafe/design/api#api-v-1-upload
            """)  # noqa
        return add_packet_cafe_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] upload file')
        packet_cafe = get_packet_cafe(self.app, parsed_args)
        # Avoid the confusing double-negative if statement
        track_status = (self.app.options.verbose_level > 0
                        and parsed_args.no_track is not True)
        fpath = parsed_args.pcap[0]
        sess_id = packet_cafe.get_session_id(
                sess_id=parsed_args.sess_id,
                reuse_session=parsed_args.reuse_session,
                choose=parsed_args.choose,
                generate=True)
        if not os.path.exists(fpath):
            raise RuntimeError(f'[-] file { fpath } not found')
        result = packet_cafe.upload(fpath=fpath, sess_id=sess_id)
        if self.app.options.verbose_level > 0:
            # NOTE(dittrich): Don't forget: 'req_id' is 'uuid' in result
            readable_result = (
                f"[+] Upload { result['filename'] }: { result['status'].lower() }\n"  # noqa
                f"[+] Session ID (sess_id): { result['sess_id'] }\n"
                f"[+] Request ID (req_id): { result['uuid'] }")
            logger.info(readable_result)
        if track_status or parsed_args.wait:
            packet_cafe.track_progress(
                sess_id=result['sess_id'],
                req_id=result['uuid'],
                debug=self.app.options.debug,
                wait_only=parsed_args.wait,
                elapsed=self.app.options.elapsed
            )


# vim: set ts=4 sw=4 tw=0 et :
