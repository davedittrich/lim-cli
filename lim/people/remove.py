# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap

from cliff.command import Command
from lim.people.pony import *


class PeopleRemove(Command):
    """Remove people."""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help='Force removal (default: False)'
        )
        parser.add_argument(
            'arg',
            nargs='*',
            default=None)
        parser.epilog = textwrap.dedent(f"""\
            Remove one or more people from the database.
            """)  # noqa
        return parser

    def take_action(self, parsed_args):
        self.log.debug('[+] removing people')
        db_connect(self.app_args.debug)
        attrs = dict()
        for arg in parsed_args.arg:
            key, value = arg.split('=')
            attrs[key] = value
            delete_person(**attrs)
            print(f"[+] successfully deleted entry with '{arg}'")


# vim: set ts=4 sw=4 tw=0 et :
