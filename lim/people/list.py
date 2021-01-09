# -*- coding: utf-8 -*-

import argparse
from lim.people import PEOPLE_ATTRIBUTES_SKIP
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
        parser.add_argument(
            '--roster',
            action='store_true',
            dest='roster',
            default=False,
            help=('Only include fields necessary for a '
                  'roster file (default: None).')
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
            default=None
        )
        parser.epilog = textwrap.dedent(
            """List people.
            """
        )
        return parser

    def take_action(self, parsed_args):
        self.log.debug('[+] listing people')
        if 'all' in parsed_args.role:
            parsed_args.role = PEOPLE_ROLES
        db_connect(debug=self.app_args.debug)
        skip = PEOPLE_ATTRIBUTES_SKIP if parsed_args.roster else []
        columns = get_people_columns(skip=skip)
        data = get_people_data(skip=skip)
        if not len(data):
            sys.exit(1)
        return columns, data


# vim: set ts=4 sw=4 tw=0 et :
