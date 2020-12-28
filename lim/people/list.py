# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap
import sys

from cliff.lister import Lister
from lim.people.pony import *


class PeopleList(Lister):
    """List people."""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '--role',
            dest='role',
            type=str,
            choices=PEOPLE_ROLES + ['all'],
            default=get_default_role(),
            help=f"Role to include or 'all' (default: '{get_default_role()}'"
        )
        find = parser.add_mutually_exclusive_group(required=False)
        find.add_argument(
            '--name-includes',
            dest='name_includes',
            default=None,
            help='Only list people whose name includes string (default: None)'
        )
        find.add_argument(
            '--email-includes',
            dest='email_includes',
            default=None,
            help=('Only list people whose email address includes '
                  'string (default: None)')
        )
        parser.add_argument(
            'id',
            nargs='*',
            default=None)
        parser.epilog = textwrap.dedent(f"""\
            List people.
            """)  # noqa
        return parser


    def take_action(self, parsed_args):
        self.log.debug('[+] listing people')
        if 'all' in parsed_args.role:
            parsed_args.role = PEOPLE_ROLES
        db_connect(debug=self.app_args.debug)
        columns = get_people_columns()
        data = get_people_data()
        if not len(data):
            sys.exit(1)
        return columns, data


# vim: set ts=4 sw=4 tw=0 et :
