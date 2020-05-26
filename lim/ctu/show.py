# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap

from cliff.show import ShowOne
from lim.ctu import CTU_Dataset


class CTUShow(ShowOne):
    """Show scenario details."""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        cache_file = CTU_Dataset.get_cache_file()
        parser.add_argument(
            '--cache-file',
            action='store',
            dest='cache_file',
            default=cache_file,
            help=('Cache file path for CTU metadata '
                  '(Env: ``LIM_CTU_CACHE``; '
                  f'default: { cache_file })')
        )
        parser.add_argument(
            '--ignore-cache',
            action='store_true',
            dest='ignore_cache',
            default=False,
            help="Ignore any cached results (default: False)"
        )
        parser.add_argument(
            'scenario',
            nargs='?',
            default=None)
        parser.epilog = textwrap.dedent("""\
           Shows details about a scenario.

           Argument is the scenario name using either the full name
           form (e.g., ``CTU-Malware-Capture-Botnet-123-1``) or an
           abbreviated form (e.g., ``Botnet-123-1``).
           """)
        return parser

    def take_action(self, parsed_args):
        self.log.debug('[+] showing scenario details')
        if 'ctu_metadata' not in dir(self):
            self.ctu_metadata = CTU_Dataset(
                cache_file=parsed_args.cache_file,
                ignore_cache=parsed_args.ignore_cache,
                debug=self.app_args.debug)
        self.ctu_metadata.load_ctu_metadata()
        columns = self.ctu_metadata.columns
        fullname = self.ctu_metadata.get_fullname(
            parsed_args.scenario)
        scenario = self.ctu_metadata.get_scenario(fullname)
        if scenario is None:
            raise RuntimeError(
                f'[-] scenario "{ parsed_args.scenario }" not found')
        scenario['SCENARIO'] = fullname
        scenario['SCENARIO_URL'] = self.ctu_metadata.get_scenario_attribute(
            name=fullname, attribute='URL')
        data = [scenario.get(i) for i in columns]
        return columns, data


# vim: set ts=4 sw=4 tw=0 et :
