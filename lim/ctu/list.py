# -*- coding: utf-8 -*-

import argparse
import logging
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
            '--fullnames',
            action='store_true',
            dest='fullnames',
            default=False,
            help="Show full names including the " +
                 "'{}' prefix".format(CTU_Dataset.__CTU_PREFIX__)
        )
        parser.add_argument(
            '--everything',
            action='store_true',
            dest='everything',
            default=False,
            help="Show all metadata attributes for scenarios " +
                 "(default : False)"
        )
        parser.add_argument(
            '--group',
            action='append',
            dest='groups',
            type=str,
            choices=CTU_Dataset.get_groups() + ['all'],
            default=None,
            help="Dataset group to incldue or 'all' " +
                 "(default: '{}')".format(CTU_Dataset.get_default_group())
        )
        find = parser.add_mutually_exclusive_group(required=False)
        find.add_argument(
            '--hash',
            dest='hash',
            metavar='<{md5|sha1|sha256} hash>',
            default=None,
            help=('Only list scenarios that involve a '
                  'specific hash (default: None)')
        )
        find.add_argument(
            '--name-includes',
            dest='name_includes',
            metavar='<string>',
            default=None,
            help=('Only list scenarioes including this string'
                  'in the "PROBABLE_NAME" (default: None)')
        )
        find.add_argument(
            '--description-includes',
            dest='description_includes',
            metavar='<string>',
            default=None,
            help=('Only list scenarioes including this string'
                  'in the description (default: None)')
        )
        parser.add_argument(
            'scenario',
            nargs='*',
            default=None)
        parser.epilog = textwrap.dedent(f"""\
           The ``--group`` option can be repeated multiple times to include multiple
           subgroups, or you can use ``--group all`` to include all groups.

           The ``--hash`` option makes an exact match on any one of the stored hash
           values.  This is the hash of the executable binary referenced in the
           ``ZIP`` column.

           The ``--name-includes`` option is rather simplistic, matching any occurance
           of the substring (case insensitive) in the ``PROBABLE_NAME`` field.  For more
           accurate matching, you can use something like the ``-f csv`` option and then
           match on regular expressions using one of the ``grep`` variants.  Or add
           regular expression handling and submit a pull request! ;)

           Valid column labels for options ``-c``, ``--column``, ``--sort-column``:
           { ", ".join([f'``{ i }``' for i in CTU_Dataset.get_columns()]) }

           Subset of columns shown by default:
           { ", ".join([f'``{ i }``' for i in CTU_Dataset.get_columns()[:CTU_Dataset.__MIN_COLUMNS__]]) }
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
        if parsed_args.groups is None:
            parsed_args.groups = 'all'
        if 'all' in parsed_args.groups:
            parsed_args.groups = CTU_Dataset.get_groups()
        if 'ctu_metadata' not in dir(self):
            self.ctu_metadata = CTU_Dataset(
                cache_file=parsed_args.cache_file,
                ignore_cache=parsed_args.ignore_cache,
                debug=self.app_args.debug)
        self.ctu_metadata.load_ctu_metadata()

        if parsed_args.everything:
            columns = self.ctu_metadata.columns
        else:
            columns = self.ctu_metadata.columns[:self.ctu_metadata.__MIN_COLUMNS__]  # noqa
        results = self.ctu_metadata.get_metadata(
            groups=parsed_args.groups,
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
        return columns, data

# vim: set ts=4 sw=4 tw=0 et :
