# -*- coding: utf-8 -*-

import argparse
import logging
import sys
import textwrap

from cliff.show import ShowOne
from lim.ctu import (
    normalize_ctu_name,
    CTU_Dataset
)


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
            nargs='?',
            type=normalize_ctu_name,
            default=None)
        parser.epilog = textwrap.dedent("""\
            Shows details about an individual scenario in tabular form.

            See ``lim ctu list --help`` for more on the ``scenario`` argument.

            ::

                $ lim ctu show iot-3-1
                +----------------+----------------------------------------------------------------------------------+
                | Field          | Value                                                                            |
                +----------------+----------------------------------------------------------------------------------+
                | Infection_Date | 2018-05-19                                                                       |
                | Capture_Name   | CTU-IoT-Malware-Capture-3-1                                                      |
                | Malware        | Muhstik                                                                          |
                | MD5            | b8849fe97e39ae3afd6def618568bb09                                                 |
                | SHA256         | 5ce13670bc875e913e6f087a4ac0a9e343347d5babb3b5c63e1d1b199371f69a                 |
                | Capture_URL    | https://mcfp.felk.cvut.cz/publicDatasets/IoTDatasets/CTU-IoT-Malware-Capture-3-1 |
                | ZIP            | fce7b8bbd1c1fba1d75b9dc1a60b25f49f68c9ec16b3656b52ed28290fc93c72.zip             |
                | LABELED        | None                                                                             |
                | BINETFLOW      | 2018-05-21_capture.binetflow                                                     |
                | PCAP           | 2018-05-21_capture.pcap                                                          |
                | WEBLOGNG       | 2018-05-21_capture.weblogng                                                      |
                +----------------+----------------------------------------------------------------------------------+

           """)  # noqa
        return parser

    def take_action(self, parsed_args):
        self.log.debug('[+] showing scenario details')
        if 'ctu_metadata' not in dir(self):
            self.ctu_metadata = CTU_Dataset(
                cache_file=parsed_args.cache_file,
                ignore_cache=parsed_args.ignore_cache,
                debug=self.app_args.debug)
        self.ctu_metadata.load_ctu_metadata()
        fullname = self.ctu_metadata.get_fullname(
            name=parsed_args.scenario)
        if not self.ctu_metadata.is_valid_scenario(fullname):
            sys.exit(1)
        columns = self.ctu_metadata.get_extended_columns()
        data = self.ctu_metadata.get_extended_data(fullname)
        return columns, data


# vim: set ts=4 sw=4 tw=0 et :
