# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap

from cliff.command import Command
from lim.people.pony import *


class PeopleUpdate(Command):
    """Update people."""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            'id',
            nargs=1,
            default=None)
        parser.add_argument(
            'arg',
            nargs='*',
            default=None)
        parser.epilog = textwrap.dedent("""\
            Update a Person entry.
            """)
        return parser

    def take_action(self, parsed_args):
        self.log.debug('[+] updating people')
        db = db_connect(self.app_args.debug)
        person_id = parsed_args.id[0]
        update_person(person_id=person_id,
                      args=parsed_args.arg)
        self.log.info(f"[+] successfully updated entry for id '{person_id}'")


# vim: set ts=4 sw=4 tw=0 et :
