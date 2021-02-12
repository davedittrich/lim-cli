# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap

from cliff.command import Command
from lim import add_browser_options
from lim import open_browser
from lim.ctu import (
    normalize_ctu_name,
    CTU_Dataset
)


class CTUOverview(Command):
    """Get CTU dataset overview."""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser = add_browser_options(parser)
        cache_file = CTU_Dataset.get_cache_file()
        parser.add_argument(
            '--cache-file',
            action='store',
            dest='cache_file',
            default=cache_file,
            help=('Cache file path for CTU metadata '
                  '(Env: ``LIM_CTU_CACHE``; '
                  f'default: ``{cache_file}``)')
        )
        parser.add_argument(
            '--ignore-cache',
            action='store_true',
            dest='ignore_cache',
            default=False,
            help="Ignore any cached results (default: ``False``)"
        )
        parser.add_argument(
            'scenario',
            nargs='*',
            type=normalize_ctu_name,
            default=None)
        parser.epilog = textwrap.dedent("""\
            Opens a browser for the web page containing the scenario
            descriptions and data links.

            Arguments are scenario names using either the full name
            form (e.g., ``CTU-Malware-Capture-Botnet-123-1``) or an
            abbreviated form (e.g., ``Botnet-123-1``).

            The URL to use is the one seen in the ``SCENARIO_URL`` column
            of the output of the ``lim ctu list`` command.

            To see help information about how the browser option works and
            how you can configure it, see ``lim about --help``.
            """)
        return parser

    def take_action(self, parsed_args):
        self.log.debug('[+] showing overview of CTU datasets')
        # TODO(dittrich): Getting really not DRY: Move this into class.
        pages = []
        # Expand scenario names if abbreviated
        scenarios = [CTU_Dataset.get_fullname(name=s)
                     for s in parsed_args.scenario]
        if 'ctu_metadata' not in dir(self):
            self.ctu_metadata = CTU_Dataset(
                cache_file=parsed_args.cache_file,
                ignore_cache=parsed_args.ignore_cache,
                debug=self.app_args.debug)
        self.ctu_metadata.load_ctu_metadata()
        if len(scenarios) == 0:
            print("{}".format(CTU_Dataset.get_disclaimer()))
            pages.append(CTU_Dataset.get_ctu_datasets_overview_url())
        else:
            for scenario in scenarios:
                page = self.ctu_metadata.get_scenario_data(scenario,
                                                           'Capture_URL')
                if page is not None:
                    pages.append(page)
        for page in pages:
            open_browser(page=page,
                         browser=parsed_args.browser,
                         force=parsed_args.force)


# vim: set ts=4 sw=4 tw=0 et :
