# -*- coding: utf-8 -*-

import argparse
import json
import logging
import textwrap
import sys

from cliff.command import Command
from lim.people import PEOPLE_ATTRIBUTES_SKIP
from lim.people.pony import *
from pony.orm.dbapiprovider import IntegrityError


class PeopleAdd(Command):
    """Add people."""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '--roster-file',
            action='store',
            dest='roster_file',
            default=None,
            help='JSON file with roster of participants (default: None).'
        )
        parser.add_argument(
            'arg',
            nargs='*',
            default=None
        )
        parser.epilog = textwrap.dedent("""\
           Add people.
           """)
        return parser

    def take_action(self, parsed_args):
        self.log.debug('[+] adding people')
        users = list()
        roster_file = parsed_args.roster_file
        if roster_file is not None:
            try:
                with open(roster_file, 'r') as f:
                    roster_str = f.read()
                users = json.loads(roster_str)
            except Exception as err:
                sys.exit(str(err))
        else:
            attrs = dict()
            for arg in parsed_args.arg:
                key, value = arg.split('=')
                attrs[key] = value
            users.append(attrs)
        db_connect(self.app_args.debug)
        for user in users:
            attrs = {
                k: v for (k, v) in user.items()
                if k not in PEOPLE_ATTRIBUTES_SKIP
            }
            try:
                new_id = add_person(**attrs)
                self.log.info(
                    '[+] successfully added person '
                    f"'{attrs.get('short_name')}' [id: {new_id}]")
            except IntegrityError as err:
                msg = str(err)
                if msg.find(':') > 0:
                    why, what = str(err).split(': ')
                    key = what.replace('Person.', '')
                    if why == 'UNIQUE constraint failed':
                        dupe_msg = (
                            f"[-] an entry with '{key}={attrs.get(key)}' "
                            "already exists")
                        if parsed_args.roster is not None:
                            self.log.info(f"{dupe_msg}: skipping")
                        else:
                            sys.exit(dupe_msg)
                else:
                    sys.exit(str(err))


# vim: set ts=4 sw=4 tw=0 et :
