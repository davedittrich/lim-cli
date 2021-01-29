# -*- coding: utf-8 -*-

import argparse
import logging
import sys
import textwrap

from cliff.lister import Lister
from lim.ctu import CTU_Dataset


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
            '--fullnames',
            action='store_true',
            dest='fullnames',
            default=False,
            help=("Show full names")
        )
        parser.add_argument(
            '--everything',
            action='store_true',
            dest='everything',
            default=False,
            help=("Show all metadata columns "
                  "(default : False)")
        )
        find = parser.add_mutually_exclusive_group(required=False)
        find.add_argument(
            '--hash',
            dest='hash',
            metavar='<{md5_hash|sha256_hash}>',
            default=None,
            help=('Only list scenarios that involve a '
                  'specific hash (default: ``None``)')
        )
        find.add_argument(
            '--name-includes',
            dest='name_includes',
            metavar='<string>',
            default=None,
            help=('Only list scenario including this string'
                  "in the 'Capture_Name' column (default: ``None``)")
        )
        find.add_argument(
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
            default=None)
        parser.epilog = textwrap.dedent(f"""\
            List scenarios (a.k.a., "captures") and related metadata.

            By default, all scenarios are listed. You can limit the output
            in several ways: by ``Capture_Name`` field; by one of a set
            of attributes; by limiting the number of items shown.

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

                $ lim ctu list -a IoT-34-1 --fit-width
                +----------------+-----------------+---------+-----------------+-----------------+---------------------+------+---------+-----------+------+----------+
                | Infection_Date | Capture_Name    | Malware | MD5             | SHA256          | Capture_URL         | ZIP  | LABELED | BINETFLOW | PCAP | WEBLOGNG |
                +----------------+-----------------+---------+-----------------+-----------------+---------------------+------+---------+-----------+------+----------+
                | 2018-12-21     | CTU-IoT-        | Mirai   | 82062b666f09fc5 | 49fd1cb22e0325c | https://mcfp.felk.c | None | None    | None      | None | None     |
                |                | Malware-        |         | c0fe4f68d1ea909 | 1f9038160da534f | vut.cz/publicDatase |      |         |           |      |          |
                |                | Capture-34-1    |         | 16              | c23672e5509e903 | ts/IoTDatasets/CTU- |      |         |           |      |          |
                |                |                 |         |                 | a94ce5bcddc893e | IoT-Malware-        |      |         |           |      |          |
                |                |                 |         |                 | b2c0            | Capture-34-1        |      |         |           |      |          |
                +----------------+-----------------+---------+-----------------+-----------------+---------------------+------+---------+-----------+------+----------+


            There are also a number of filters that can be applied, including MD5
            and SHA256 hash, substrings in the ``Capture_Name`` or ``Malware``
            fields, or description of the scenario in its web page.

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
        # Expand scenario names if abbreviated
        scenarios = [CTU_Dataset.get_fullname(s)
                     for s in parsed_args.scenario]
        # Defaulting doesn't work right with append, so set
        # default here.
        if 'ctu_metadata' not in dir(self):
            self.ctu_metadata = CTU_Dataset(
                cache_file=parsed_args.cache_file,
                ignore_cache=parsed_args.ignore_cache,
                debug=self.app_args.debug)
        self.ctu_metadata.load_ctu_metadata()

        # if parsed_args.everything:
        #     columns = self.ctu_metadata.columns
        # else:
        #     columns = self.ctu_metadata.columns[:self.ctu_metadata.__MIN_COLUMNS__]  # noqa
        columns = self.ctu_metadata.columns
        results = self.ctu_metadata.get_metadata(
            columns=columns,
            name_includes=parsed_args.name_includes,
            fullnames=parsed_args.fullnames,
            description_includes=parsed_args.description_includes,
            has_hash=parsed_args.hash)
        data = []
        if len(scenarios) > 0:
            data = [r for r in results
                    if CTU_Dataset.get_fullname(r[0]) in scenarios]
        else:
            if self.app_args.limit > 0:
                data = results[0:min(self.app_args.limit, len(results))]
            else:
                data = results
        if not len(data):
            sys.exit(1)
        return columns, data

# vim: set ts=4 sw=4 tw=0 et :
