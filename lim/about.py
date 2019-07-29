# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap

from cliff.command import Command
from lim import __version__
from lim.ctu import __DISCLAIMER__


class About(Command):
    """About the ``lim`` CLI"""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(About, self).get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.epilog = textwrap.dedent("""
            .. code-block:: console

                $ lim about
                lim version {VERSION}

                {DISCLAIMER}

            ..
            """.format(VERSION=__version__, DISCLAIMER=__DISCLAIMER__)
        )

        return parser

    def take_action(self, parsed_args):
        print("lim version {VERSION}\n\n{DISCLAIMER}".format(
            VERSION=__version__, DISCLAIMER=__DISCLAIMER__))


# EOF
