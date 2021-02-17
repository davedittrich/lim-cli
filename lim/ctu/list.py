# -*- coding: utf-8 -*-

import argparse
import arrow
import logging
import sys
import textwrap

from cliff.lister import Lister
from lim.ctu import (
    normalize_ctu_name,
    CTU_Dataset
)


class CTUList(Lister):
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
            '--date-starting',
            dest='date_starting',
            metavar='<YYYY-MM-DD>',
            default='1970-01-01',
            help=('List scenarios starting from this date '
                  "(default: '1970-01-01')")
        )
        TODAY_DATE = arrow.now().format('YYYY-MM-DD')
        parser.add_argument(
            '--date-ending',
            dest='date_ending',
            metavar='<YYYY-MM-DD>',
            default=TODAY_DATE,
            help=('List scenarios up to this date '
                  f"(default: '{TODAY_DATE}')")
        )
        parser.add_argument(
            '--fullnames',
            action='store_true',
            dest='fullnames',
            default=False,
            help=("Show full names")
        )
        parser.add_argument(
            '-a', '--everything',
            action='store_true',
            dest='everything',
            default=False,
            help=("Show all metadata columns "
                  "(default : False)")
        )
        parser.add_argument(
            '--hash',
            dest='hash',
            metavar='<{md5_hash|sha256_hash}>',
            default=None,
            help=('Only list scenarios that involve a '
                  'specific hash (default: ``None``)')
        )
        parser.add_argument(
            '--malware-includes',
            dest='malware_includes',
            metavar='<string>',
            default=None,
            help=('Only list scenarios including this string'
                  "in the 'Malware' column (default: ``None``)")
        )
        parser.add_argument(
            '--name-includes',
            dest='name_includes',
            metavar='<string>',
            default=None,
            help=('Only list scenario including this string'
                  "in the 'Capture_Name' column (default: ``None``)")
        )
        parser.add_argument(
            '--description-includes',
            dest='description_includes',
            metavar='<string>',
            default=None,
            help=('Only list scenarios including this string'
                  'in the description (default: ``None``)')
        )
        parser.add_argument(
            'scenario',
            nargs='*',
            type=normalize_ctu_name,
            default=None)
        all_columns = ", ".join(
            [f'{i.lower()}' for i in CTU_Dataset.get_all_columns()])
        default_columns = ", ".join(
            [f"{i.lower()}" for i in CTU_Dataset.get_index_columns()]
        )
        parser.epilog = textwrap.dedent(f"""\
            List scenarios (a.k.a., "captures") and related metadata.

            By default, all scenarios are listed. You can limit the output
            by filtering on several attributes (e.g., by ``Capture_Name``
            field, by date range, contents of the malware name or web page
            description, etc.) You can also limit the number of items
            shown if necessary when the number of results is large.

            The ``scenario`` argument equates to the field ``Capture_Name`` in
            the index. This can be the scenario's full name (e.g.,
            ``CTU-IoT-Malware-Capture-34-1``) or an abbreviated form of the
            name (e.g., ``IoT-34-1`` or just ``34-1``).

            ::

                $ lim ctu list IoT-34-1 Botnet-42
                +----------------+-------------------------------+---------+
                | Infection_Date | Capture_Name                  | Malware |
                +----------------+-------------------------------+---------+
                | 2011-08-10     | CTU-Malware-Capture-Botnet-42 | Neeris  |
                | 2018-12-21     | CTU-IoT-Malware-Capture-34-1  | Mirai   |
                +----------------+-------------------------------+---------+


            A larger number of attributes are available. You can get all of them
            using the ``-a`` (``--everything``) flag. The subset of columns shown
            by default is: ``{default_columns}``

            Valid column labels for options ``-c``, ``--column``, ``--sort-column``,
            or to be shown with ``-a``, include:
            ``{all_columns}``

            Using ``lim ctu list -a`` produces very wide output. Even if many fields
            are ``None`` and ``--fit-width`` is included, it is still unwieldy for just
            one scenario as you can see here. Consider using ``lim ctu show`` instead.

            ::

                $ lim ctu list --name-includes IoT --malware-includes muhstik --fit-width -a
                +----------------+------------------------+---------+------------------------+------------------------+------------------------+------------------------+---------+------------------------+------------------------+-----------------------------+
                | Infection_Date | Capture_Name           | Malware | MD5                    | SHA256                 | Capture_URL            | ZIP                    | LABELED | BINETFLOW              | PCAP                   | WEBLOGNG                    |
                +----------------+------------------------+---------+------------------------+------------------------+------------------------+------------------------+---------+------------------------+------------------------+-----------------------------+
                | 2018-05-19     | CTU-IoT-Malware-       | Muhstik | b8849fe97e39ae3afd6def | 5ce13670bc875e913e6f08 | https://mcfp.felk.cvut | fce7b8bbd1c1fba1d75b9d | None    | 2018-05-21_capture.bin | 2018-05-21_capture.pca | 2018-05-21_capture.weblogng |
                |                | Capture-3-1            |         | 618568bb09             | 7a4ac0a9e343347d5babb3 | .cz/publicDatasets/IoT | c1a60b25f49f68c9ec16b3 |         | etflow                 | p                      |                             |
                |                |                        |         |                        | b5c63e1d1b199371f69a   | Datasets/CTU-IoT-      | 656b52ed28290fc93c72.z |         |                        |                        |                             |
                |                |                        |         |                        |                        | Malware-Capture-3-1    | ip                     |         |                        |                        |                             |
                +----------------+------------------------+---------+------------------------+------------------------+------------------------+------------------------+---------+------------------------+------------------------+-----------------------------+


            There are also a number of filters that can be applied, including MD5
            and SHA256 hash, substrings in the ``Capture_Name`` or ``Malware``
            fields, start and end dates, or description of the scenario in its
            web page.

            The ``--hash`` option makes an exact match on any of the stored hash
            values.  This is the hash of the executable binary referenced in the
            ``ZIP`` column. This example uses the most frequently occuring MD5
            hash as seen in ``lim ctu stats --help``::

                $ lim ctu list --hash e515267ba19417974a63b51e4f7dd9e9
                +----------------+----------------------------------+---------+
                | Infection_Date | Capture_Name                     | Malware |
                +----------------+----------------------------------+---------+
                | 2015-03-04     | CTU-Malware-Capture-Botnet-110-1 | HTBot   |
                | 2015-03-04     | CTU-Malware-Capture-Botnet-110-2 | HTBot   |
                | 2015-03-09     | CTU-Malware-Capture-Botnet-110-3 | HTBot   |
                | 2015-03-09     | CTU-Malware-Capture-Botnet-111-2 | HTBot   |
                | 2015-04-09     | CTU-Malware-Capture-Botnet-110-4 | HTBot   |
                | 2015-04-09     | CTU-Malware-Capture-Botnet-111-3 | HTBot   |
                | 2015-04-22     | CTU-Malware-Capture-Botnet-110-5 | HTBot   |
                | 2015-04-22     | CTU-Malware-Capture-Botnet-111-4 | HTBot   |
                | 2015-04-23     | CTU-Malware-Capture-Botnet-110-6 | HTBot   |
                | 2015-06-09     | CTU-Malware-Capture-Botnet-111-5 | HTBot   |
                +----------------+----------------------------------+---------+


            The ``--malware-includes`` option is rather simplistic, matching any
            occurance of the substring (case insensitive) in the ``Malware`` field.
            The same applies for the ``--name-includes`` option with respect to the
            ``Capture_Name`` field. For more accurate matching, you may want to use
            something like the ``-f csv`` option and match on regular expressions
            using one of the ``grep`` variants.  Or add regular expression handling
            and submit a pull request! ;)
           \n""") + CTU_Dataset.get_disclaimer()  # noqa

        return parser

    # FYI, https://mcfp.felk.cvut.cz/publicDatasets/CTU-Malware-Capture-Botnet-269-1/README.html  # noqa
    # is an Emotet sample...
    # TODO(dittrich): Figure out how to handle these

    def take_action(self, parsed_args):
        self.log.debug('[+] listing CTU data')
        if 'ctu_metadata' not in dir(self):
            self.ctu_metadata = CTU_Dataset(
                cache_file=parsed_args.cache_file,
                ignore_cache=parsed_args.ignore_cache,
                debug=self.app_args.debug)
        self.ctu_metadata.load_ctu_metadata()
        # Expand capture names if abbreviated
        scenarios = []
        for scenario in parsed_args.scenario:
            full_name = self.ctu_metadata.get_fullname(name=scenario)
            if full_name is None:
                sys.exit(f"[-] '{scenario}' does not match any scenario names")
            scenarios.append(full_name)
        columns = (
            self.ctu_metadata.get_index_columns()
            if not parsed_args.everything
            else self.ctu_metadata.get_all_columns()
        )
        results = self.ctu_metadata.get_metadata(
            columns=columns,
            malware_includes=parsed_args.malware_includes,
            name_includes=parsed_args.name_includes,
            fullnames=parsed_args.fullnames,
            description_includes=parsed_args.description_includes,
            date_starting=parsed_args.date_starting,
            date_ending=parsed_args.date_ending,
            has_hash=parsed_args.hash)
        data = []
        if len(scenarios) > 0:
            for row in results:
                if row[1] in scenarios:
                    data.append(row)
        else:
            if self.app_args.limit > 0:
                data = results[0:min(self.app_args.limit, len(results))]
            else:
                data = results
        if not len(data):
            sys.exit(1)
        return columns, data

# vim: set ts=4 sw=4 tw=0 et :
