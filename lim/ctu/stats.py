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
        cache_file = CTU_Dataset.get_cache_file()
        parser.add_argument(
            '--cache-file',
            action='store',
            dest='cache_file',
            default=cache_file,
            help=('Cache file path '
                  f'(default: { cache_file })')
        )
        parser.add_argument(
            '--ignore-cache',
            action='store_true',
            dest='ignore_cache',
            default=False,
            help="Ignore any cached results (default: False)"
        )
        parser.add_argument(
            'attribute',
            nargs='?',
            default='GROUP',
            choices=CTU_Dataset.get_columns(),
            help='Attribute to quantify (default: "GROUP")'
        )
        parser.epilog = textwrap.dedent(f"""\
            Shows the selected dataset attribute and a count of unique
            instances.

            To see more detailed descriptions of the CTU datasets as a whole,
            or for specific groups, use ``lim ctu overview`` to view the
            appropriate web page.
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
        columns = (parsed_args.attribute, 'COUNT')
        count = {}
        results = [item[0] for item in self.ctu_metadata.get_metadata(
                      columns=[parsed_args.attribute],
                      fullnames=True)]
        for item in results:
            # Handle null values vs. no key (either way, be consistent)
            if item == '':
                item = None
            try:
                count[item] += 1
            except KeyError:
                count[item] = 1
        data = [(r, count[r]) for r in sorted(count,
                                              key=count.get,
                                              reverse=True)]
        return columns, data


# vim: set ts=4 sw=4 tw=0 et :
