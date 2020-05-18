# -*- encoding: utf-8 -*-

import argparse
import logging
import textwrap

from cliff.command import Command
from lim import __version__
from lim.main import copyright


class About(Command):
    """About the ``lim`` CLI"""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.epilog = textwrap.dedent(f"""
            .. code-block:: console

                $ lim about
                lim version { __version__ }

            ..

            { copyright() }
            """)  # noqa
        return parser

    def take_action(self, parsed_args):
        if (
            self.app_args.verbose_level == 0 or
            self.cmd_name == "version"
        ):
            print(f'{ __version__ }')
        else:
            print(f'lim version { __version__ }\n{ copyright() }')


# EOF
