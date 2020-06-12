# -*- coding: utf-8 -*-

from __future__ import print_function

import argparse
import logging
import sys
import textwrap
import webbrowser

from cliff.command import Command
from lim.packet_cafe import add_packet_cafe_global_options
from lim.packet_cafe import get_packet_cafe
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
            help="Browser to use for viewing (default: None)."
        )
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help=("Open the browser even if process has no TTY "
                  "(default: False)")
        )
        # NOTE(dittrich): Not DRY. Similar text in lim/packet_cafe/about.py
        parser.epilog = textwrap.dedent("""
            Opens up the packet-cafe UI in a browser.

            An exception is thrown if the process has no TTY. Use the ``--force``
            option to bypass this behavior and attempt to open the browser
            anyway.

            Use the ``--browser`` option to choose which browser from the
            set shown.  One systems that do not have any of those browsers
            available, or can't open them for some reason, the page may open
            in the ``lynx`` text browser. If you wish to choose (a) different
            browser(s), export the environment variable ``LIM_BROWSERS``
            with a comma separated list of options.

            See also: https://docs.python.org/3/library/webbrowser.html
            """)  # noqa
        return add_packet_cafe_global_options(parser)

    def take_action(self, parsed_args):
        self.log.debug('[+] opening packet-cafe UI')
        if not sys.stdin.isatty() and not parsed_args.force:
            raise RuntimeError(
                "[-] use --force to open browser when stdin is not a TTY")
        packet_cafe = get_packet_cafe(self.app, parsed_args)
        page = packet_cafe.get_ui_url()
        if parsed_args.browser is not None:
            webbrowser.get(parsed_args.browser).open_new_tab(page)
        else:
            webbrowser.open(page, new=1)


# vim: set ts=4 sw=4 tw=0 et :
