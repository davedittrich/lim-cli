# -*- coding: utf-8 -*-

from __future__ import print_function

import argparse
import logging
import textwrap

from cliff.command import Command

# Initialize a logger for this module.
logger = logging.getLogger(__name__)


class PeopleHelp(Command):
    """Help for people management."""

    log = logging.getLogger(__name__)

    HELP_TEXT = textwrap.dedent(f"""
            The ``people`` command manages metadata about people that can
            be used for deploying multi-user systems. It is not intended
            to be a complete authentication and authorization system, but
            can be used for to bootstrap a set of user accounts and/or for
            assigning cloud instances to people involved in a purpleteam
            exercise, conference training session, or CTF event.
            """)  # noqa

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.epilog = self.HELP_TEXT
        return parser

    def take_action(self, parsed_args):
        self.log.debug('[+] about people')
        print(self.HELP_TEXT)


# vim: set ts=4 sw=4 tw=0 et :
