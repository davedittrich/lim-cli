# -*- coding: utf-8 -*-

from __future__ import print_function

import argparse
import logging
import textwrap

from cliff.command import Command
from lim import add_browser_options
from lim import open_browser
from lim.packet_cafe import add_packet_cafe_global_options
from lim.packet_cafe import get_packet_cafe

# Initialize a logger for this module.
logger = logging.getLogger(__name__)


class UI(Command):
    """Open packet-cafe UI in a browser."""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser = add_browser_options(parser)
        parser.epilog = textwrap.dedent("""
            Opens up the packet-cafe UI in a browser.

            To see help information about how the browser option works and
            how you can configure it, see ``lim about --help``.
            """)  # noqa
        return add_packet_cafe_global_options(parser)

    def take_action(self, parsed_args):
        self.log.debug('[+] opening packet-cafe UI')
        packet_cafe = get_packet_cafe(self.app, parsed_args)
        open_browser(page=packet_cafe.get_ui_url(),
                     browser=parsed_args.browser,
                     force=parsed_args.force)


# vim: set ts=4 sw=4 tw=0 et :
