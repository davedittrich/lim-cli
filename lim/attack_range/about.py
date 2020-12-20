# -*- coding: utf-8 -*-

from __future__ import print_function

import argparse
import logging
import textwrap

from cliff.command import Command
from lim import add_browser_options
from lim import open_browser
from lim.attack_range import ATTACK_RANGE_REPO_URL

# Initialize a logger for this module.
logger = logging.getLogger(__name__)


class About(Command):
    """Open Splunk Attack Range documentation."""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser = add_browser_options(parser)
        # NOTE(dittrich): Text here is coupled w/ lim/__init__.py
        parser.epilog = textwrap.dedent(f"""
            Opens up the Splunk Attack Range documenation in a browser.

            .. code-block:: console

                $ lim range about
                [+] opening browser 'system default' for {ATTACK_RANGE_REPO_URL}

            ..

            To see help information about how the browser option works and
            how you can configure it, see ``lim about --help``.
            """)  # noqa
        return parser

    def take_action(self, parsed_args):
        self.log.debug('[+] opening Splunk Attack Range documentation')
        open_browser(page=ATTACK_RANGE_REPO_URL,
                     browser=parsed_args.browser,
                     force=parsed_args.force)


# vim: set ts=4 sw=4 tw=0 et :
