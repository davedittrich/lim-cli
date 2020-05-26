# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap

from cliff.command import Command
from lim.packet_cafe import add_packet_cafe_global_options
from lim.packet_cafe import check_remind_defaulting
from lim.packet_cafe import chose_wisely
from lim.packet_cafe import get_session_ids
from lim.packet_cafe import get_last_request_id
from lim.packet_cafe import get_last_session_id
from lim.packet_cafe import delete

logger = logging.getLogger(__name__)


class AdminDelete(Command):
    """Delete data for a session."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '--all',
            action='store_true',
            dest='all',
            default=False,
            help=('Delete data for all sessions (careful with that '
                  'flag, Eugene!  default: False)')
        )
        parser.add_argument(
            'sess_id', nargs='*', default=[get_last_session_id()])
        parser.epilog = textwrap.dedent("""
            Deletes all data and id directories for one or more
            sessions.

            """)  # noqa
        return add_packet_cafe_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] deleting session data')
        ids = get_session_ids()
        if ids is None or not len(ids):
            raise RuntimeError('[-] no sessions exist')
        if parsed_args.all:
            sess_ids = ids
        else:
            if parsed_args.sess_id[0] is not None:
                sess_id = check_remind_defaulting(
                    parsed_args.sess_id[0], 'last session id')
            else:
                sess_id = chose_wisely(from_list=ids,
                                       what="a session",
                                       cancel_throws_exception=True)
            if sess_id not in ids:
                raise RuntimeError(f'[-] session ID { sess_id } not found')
            sess_ids = [sess_id]
        for sess_id in sess_ids:
            result = delete(sess_id=sess_id)
            if result is None:
                raise RuntimeError('[-] failed to delete '
                                   f'session { sess_id }')
            # Do state files need to be deleted?
            # (Granted, this relies on a side-effect, but
            # c'est la vie. ¯\_(ツ)_/¯)
            _, _ = get_last_session_id(), get_last_request_id()
            logger.info(f'[+] deleted session { sess_id }')


# vim: set ts=4 sw=4 tw=0 et :
