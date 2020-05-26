# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap

from cliff.lister import Lister
from lim.packet_cafe import add_packet_cafe_global_options
from lim.packet_cafe import check_remind_defaulting
from lim.packet_cafe import choose_wisely
from lim.packet_cafe import get_requests
from lim.packet_cafe import get_session_ids
from lim.packet_cafe import get_last_session_id

logger = logging.getLogger(__name__)


class Requests(Lister):
    """List request IDs for a specific session ID."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            'sess_id', nargs='?', default=get_last_session_id())
        parser.epilog = textwrap.dedent("""
            List current request IDs for a specific packet-cafe session ID. By default,
            the last used session ID will be the default. Otherwise, specify the session ID
            as an argument

            .. code-block:: console

                $ lim cafe requests --fit-width
                [+] implicitly reusing last session id bae5d69c-7180-445d-a8db-22a5ef0872e8
                +--------------------------+--------------------------+-------------------+--------------------------+
                | Id                       | Filename                 | Original_Filename | Tools                    |
                +--------------------------+--------------------------+-------------------+--------------------------+
                | 13394ad96ef3420094387a6a | trace_13394ad96ef3420094 | test.pcap         | networkml,mercury,pcap-  |
                | a748490f                 | 387a6aa748490f_2020-05-1 |                   | stats,snort,p0f,pcapplot |
                |                          | 5_07_25_48.pcap          |                   |                          |
                +--------------------------+--------------------------+-------------------+--------------------------+


            ..

            See https://cyberreboot.gitbook.io/packet-cafe/design/api#api-v-1-ids-sess_id
            """)  # noqa
        return add_packet_cafe_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] listing request ids')
        ids = get_session_ids()
        if len(ids) == 0:
            raise RuntimeError('[-] no sessions found')
        if parsed_args.sess_id is not None and not parsed_args.choose:
            sess_id = check_remind_defaulting(
                parsed_args.sess_id, 'last session id')
        else:
            sess_id = choose_wisely(
                from_list=ids,
                what="session",
                cancel_throws_exception=True
            )
        if sess_id not in ids:
            raise RuntimeError(f'[-] session ID { sess_id } not found')
        #
        # NOTE(dittrich): The dictionary key "original_filename" differs
        # from other dictionaries that have "camel case" (e.g.,
        # "viewableOutput" in the tools list), which complicates
        # capitalization of column headers. :(
        columns = ['Id', 'Filename', 'Original_Filename', 'Tools']
        data = []
        for row in get_requests(sess_id=sess_id):
            data.append(
                ([row[c.lower()] for c in columns])
            )
        return (columns, data)


# vim: set ts=4 sw=4 tw=0 et :
