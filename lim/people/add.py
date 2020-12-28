# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap
import sys

from cliff.command import Command
from lim.people.pony import *
from pony.orm.dbapiprovider import IntegrityError


class PeopleAdd(Command):
    """Add people."""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            'arg',
            nargs='*',
            default=None)
        parser.epilog = textwrap.dedent("""\
           Add people.
           """)
        return parser

    def take_action(self, parsed_args):
        self.log.debug('[+] adding people')
        attrs = dict()
        for arg in parsed_args.arg:
            key, value = arg.split('=')
            attrs[key] = value
        db = db_connect(self.app_args.debug)
        try:
            new_id = add_person(**attrs)
        except IntegrityError as err:
            msg = str(err)
            if msg.find(':') > 0:
                why, what = str(err).split(': ')
                key = what.replace('Person.', '')
                if why == 'UNIQUE constraint failed':
                    sys.exit(
                        f"[-] an entry with '{key}={attrs.get(key)}' "
                        "already exists")
            sys.exit(str(err))
        self.log.info(f"[+] successfully added person [id: {new_id}]")


# vim: set ts=4 sw=4 tw=0 et :
