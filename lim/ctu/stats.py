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
                  f'(default: ``{cache_file}``)')
        )
        parser.add_argument(
            '--ignore-cache',
            action='store_true',
            dest='ignore_cache',
            default=False,
            help="Ignore any cached results (default: ``False``)"
        )
        attributes = ", ".join(
            [c.lower() for c in CTU_Dataset.get_index_columns(min=False)]
        )
        parser.add_argument(
            'attribute',
            nargs='?',
            default='infection_date',
            choices=[
                c.lower()
                for c in CTU_Dataset.get_index_columns(min=False)
            ],
            help='Attribute to quantify (default: ``infection_date``)'
        )
        parser.epilog = textwrap.dedent(f"""\
            Shows the selected dataset attribute and a count of unique
            instances in reverse order of occurance.

            ::

                $ lim ctu stats md5 | head
                +----------------------------------+-------+
                | MD5                              | Count |
                +----------------------------------+-------+
                | e515267ba19417974a63b51e4f7dd9e9 |    10 |
                | -                                |     9 |
                | e1090d7126dd88d0d1d39b68ea3aae11 |     6 |
                | 05a00c320754934782ec5dec1d5c0476 |     6 |
                | 48616dd47e12e369feef53a57830158a |     5 |
                | 11bc606269a161555431bacf37f7c1e4 |     5 |
                | bf08e6b02e00d2bc6dd493e93e69872f |     4 |


            Possible attributes are those that come from the CTU index
            file (``{attributes}``).

            To see more detailed descriptions of the CTU datasets as a whole,
            use ``lim ctu overview`` to view the appropriate web page.
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
        columns = (
            self.ctu_metadata.get_column_string(parsed_args.attribute),
            'Count'
        )
        count = {}
        results = [
            item[0] for item in self.ctu_metadata.get_metadata(
                columns=[parsed_args.attribute],
                fullnames=True)
        ]
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
