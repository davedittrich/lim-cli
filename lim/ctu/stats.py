# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap

from cliff.lister import Lister
from lim.ctu import CTU_Dataset


class CTUStats(Lister):
    """List CTU dataset metadata."""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '--cache-file',
            action='store',
            dest='cache_file',
            default=None,
            help="Cache file path (default: None)."
        )
        parser.add_argument(
            '--ignore-cache',
            action='store_true',
            dest='ignore_cache',
            default=False,
            help="Ignore any cached results (default: False)."
        )
        parser.epilog = textwrap.dedent("""\
            Shows the groups and counts of members in each dataset group.

            To see more detailed descriptions of the CTU datasets as a whole,
            or for specific groups, use ``lim ctu overview`` to go to the appropriate
            web page.
           """)  # noqa
        return parser

    def take_action(self, parsed_args):
        self.log.debug('[+] showing CTU data statistics')
        if 'ctu_metadata' not in dir(self):
            self.ctu_metadata = CTU_Dataset(
                cache_file=parsed_args.cache_file,
                ignore_cache=parsed_args.ignore_cache,
                debug=self.app_args.debug)
        self.ctu_metadata.load_ctu_metadata()
        columns = ('GROUP', 'COUNT')
        count = dict()
        for k, v in self.ctu_metadata.scenarios.items():
            try:
                count[v['GROUP']] += 1
            except KeyError:
                count[v['GROUP']] = 1
        data = [(r, count[r]) for r in count]
        return columns, data


# vim: set ts=4 sw=4 tw=0 et :
