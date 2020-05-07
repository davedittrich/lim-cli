# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap

from cliff.lister import Lister
from lim.packet_cafe import chose_wisely
from lim.packet_cafe import get_ids
from lim.packet_cafe import get_ids_for_session

logger = logging.getLogger(__name__)


class Requests(Lister):
    """List request IDs for a specific session ID."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument('sess_id', nargs='?', default=None)
        parser.epilog = textwrap.dedent("""
            List current request IDs for a specific packet-cafe session ID.

            See https://cyberreboot.gitbook.io/packet-cafe/design/api#api-v-1-ids-sess_id
            """)  # noqa
        return parser

    def take_action(self, parsed_args):
        logger.debug('[+] listing request ids')
        ids = get_ids()
        if parsed_args.sess_id is not None:
            sess_id = parsed_args.sess_id
        else:
            sess_id = chose_wisely(from_list=ids, what="session")
        if sess_id not in ids:
            raise RuntimeError(f'Session ID { sess_id } not found')
        #
        # NOTE(dittrich): The dictionary key "original_filename" differs
        # from other dictionaries that have "camel case" (e.g.,
        # "viewableOutput" in the tools list), which complicates
        # capitalization of column headers. :(
        columns = ['Id', 'Filename', 'Original_Filename', 'Tools']
        data = list()
        for row in get_ids_for_session(sess_id=sess_id):
            data.append(
                ([row[c.lower()] for c in columns])
            )
        return (columns, data)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
