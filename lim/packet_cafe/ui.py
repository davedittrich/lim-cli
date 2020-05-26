# -*- coding: utf-8 -*-

from __future__ import print_function

import argparse
import logging
import textwrap
import webbrowser

from cliff.command import Command
from lim.packet_cafe import CAFE_UI_URL
from lim.packet_cafe import __BROWSERS__

# Initialize a logger for this module.
logger = logging.getLogger(__name__)


class UI(Command):
    """Open packet-cafe UI in a browser."""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '--browser',
            action='store',
            dest='browser',
            choices=__BROWSERS__,
            default=None,
            help="Browser to use for viewing " +
                 "(default: {}).".format(None)
        )
        # NOTE(dittrich): Not DRY. Similar text in lim/packet_cafe/about.py
        parser.epilog = textwrap.dedent("""
            Opens up the packet-cafe UI in a browser.

            Use the ``--browser`` option to choose which browser from the
            set shown.  One systems that do not have any of those browsers
            available, or can't open them for some reason, the page may open
            in the ``lynx`` text browser. If you wish to choose (a) different
            browser(s), export the environment variable ``LIM_BROWSERS``
            with a comma separated list of options.

            See also: https://docs.python.org/3/library/webbrowser.html
            """)  # noqa
        return parser

    def take_action(self, parsed_args):
        self.log.debug('[+] opening packet-cafe UI')
        page = CAFE_UI_URL
        if parsed_args.browser is not None:
            webbrowser.get(parsed_args.browser).open_new_tab(page)
        else:
            webbrowser.open(page, new=1)


# vim: set ts=4 sw=4 tw=0 et :
