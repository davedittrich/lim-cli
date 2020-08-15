# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap

from cliff.command import Command
from lim.packet_cafe import add_packet_cafe_global_options
from lim.packet_cafe import check_remind_defaulting
from lim.packet_cafe import choose_wisely
from lim.packet_cafe import get_packet_cafe
from lim.packet_cafe import NO_SESSIONS_MSG

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
        parser.add_argument('sess_id', nargs='*', default=[])
        parser.epilog = textwrap.dedent("""
            Deletes all data and id directories for one or more
            sessions.

            As a safety feature, you must provide a session ID
            on the command line or choose interactively. This command
            will not default like other commands.

            To select specific sessions, provide them as arguments.
            You can select the desired session ID from a list of
            available sessions with the ``--choose`` option, or
            delete all sessions at once with ``--all``:

            .. code-block:: console

                $ lim cafe admin delete --all
                [+] deleted session 531f8bad-1f01-4b10-926b-a72aa27bcdba
                [+] deleted session e6129371-ab97-4225-940e-5b18cd761da7
                [+] deleted session 46d4f9a9-d5db-487e-a261-91764c044b44
                [+] deleted session f44dc0e5-2ad0-4cbd-aac9-98a6c8233dff
                [+] deleted session 5382b1b3-39f2-4563-9486-8efb99b56243

            ..
            """)  # noqa
        return add_packet_cafe_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] deleting session data')
        packet_cafe = get_packet_cafe(self.app, parsed_args)
        ids = packet_cafe.get_session_ids()
        if ids is None or not len(ids):
            raise RuntimeError(NO_SESSIONS_MSG)
        if parsed_args.all:
            sess_ids = ids
        else:
            if (
                len(parsed_args.sess_id)
                and parsed_args.sess_id[0] is not None
                and not parsed_args.choose
            ):
                sess_id = check_remind_defaulting(
                    parsed_args.sess_id[0], 'last session id')
            else:
                sess_id = choose_wisely(from_list=ids,
                                        what="a session",
                                        cancel_throws_exception=True)
            if sess_id not in ids:
                raise RuntimeError(f'[-] session ID { sess_id } not found')
            sess_ids = [sess_id]
        for sess_id in sess_ids:
            result = packet_cafe.delete(sess_id=sess_id)
            if result is None:
                raise RuntimeError('[-] failed to delete '
                                   f'session { sess_id }')
            # Do state files need to be deleted?
            # (Granted, this relies on a side-effect, but
            # c'est la vie. ¯\_(ツ)_/¯ )
            _, _ = packet_cafe.get_last_session_id(), packet_cafe.get_last_request_id()  # noqa
            logger.info(f'[+] deleted session { sess_id }')


# vim: set ts=4 sw=4 tw=0 et :
