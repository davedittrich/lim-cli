# -*- coding: utf-8 -*-

import argparse
import logging
import os
import textwrap
import subprocess  # nosec
import sys

from cliff.command import Command
from lim.ctu import CTU_Dataset
from lim import DEFAULT_PROTOCOLS


class CTUGet(Command):
    """Get CTU dataset components."""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help="Force over-writing files if they exist (default: False)"
        )
        parser.add_argument(
            '--no-subdir',
            action='store_true',
            dest='no_subdir',
            default=False,
            help=('Do not maintain scenario name subdirectory '
                  '(default: False)')
        )
        _default_protocols = ",".join(DEFAULT_PROTOCOLS)
        parser.add_argument(
            '-P', '--protocols',
            metavar='<protocol-list>',
            dest='protocols',
            type=lambda s: [i for i in s.split(',')],
            default=_default_protocols,
            help='Protocols to include, or "any" ' +
                 '(default: {})'.format(_default_protocols)
        )
        parser.add_argument(
            '-L', '--maxlines',
            metavar='<lines>',
            dest='maxlines',
            default=None,
            help="Maximum number of lines to get (default: None)"
        )
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
            'name',
            nargs=1,
            default=None)
        parser.add_argument(
            'data',
            nargs='+',
            type=str.upper,
            choices=CTU_Dataset.get_attributes() + ['ALL'],
            default=None)
        parser.epilog = textwrap.dedent(f"""\
            Get one or more data components from a scenario. These
            components are the raw PCAP file, Netflow file, and
            other analytic products from intrusion detection system
            processing, etc.

            Use ``ALL`` to recursively download all scenario data, or
            one of the attribute types: { ", ".join([f'``{ i }``' for i in CTU_Dataset.get_attributes()]) }

            By default, or when using the ``ALL`` attribute identifier,
            the file(s) are placed in a subdirectory with the full name
            of the scenario to better organize data across multiple
            scenarios. You can override this when getting specific files
            (i.e., not using ``ALL``) with the ``--no-subdir``
            option. Files will then be placed in the lace specified files in

           \n""") + CTU_Dataset.get_disclaimer()  # noqa
        return parser

    def take_action(self, parsed_args):
        self.log.debug('[+] getting CTU data')
        if 'ctu_metadata' not in dir(self):
            self.ctu_metadata = CTU_Dataset(
                cache_file=parsed_args.cache_file,
                ignore_cache=parsed_args.ignore_cache,
                debug=self.app_args.debug)
            # TODO(dittrich): Work this back into init() method.
        self.ctu_metadata.load_ctu_metadata()

        name = CTU_Dataset.get_fullname(parsed_args.name[0])
        if not self.ctu_metadata.is_valid_scenario(name):
            raise RuntimeError(f'[-] scenario "{ name }" does not exist')
        if parsed_args.no_subdir is False:
            data_dir = name
        else:
            data_dir = self.app_args.data_dir
        if 'ALL' in parsed_args.data:
            self.recursive_get_all(name)
        else:
            for attribute in parsed_args.data:
                self.log.debug(
                    f'[+] downloading { attribute } data '
                    f'for scenario { name }')
                self.ctu_metadata.fetch_scenario_content_byattribute(
                    data_dir=data_dir, name=name, attribute=attribute)

    def recursive_get_all(self,
                          name,
                          cwd=os.getcwd(),
                          stderr=subprocess.STDOUT,
                          shell=False):
        """Use wget to recursively get all scenario data."""
        cmd = ['wget', '-h']
        result = ""
        try:
            result = subprocess.check_output(  # nosec
                    cmd,
                    cwd=cwd,
                    stderr=stderr,
                    shell=shell
                ).decode('UTF-8').splitlines()
        except Exception as err:
            message = f'[-] cannot run "wget": { err }'
        else:
            message = '[-] cannot run "wget"'
        if len(result) > 1 and result[0].find(' Wget ') < 0:
            raise RuntimeError(message)

        url = self.ctu_metadata.get_scenario_attribute(
                name=name, attribute='URL')
        cmd = ['wget',
               '-r',
               '--no-parent',
               '--no-host-directories',
               '--cut-dirs=1',
               '--no-check-certificate']
        cmd.append(url)
        """Use subprocess.check_ouput to run subcommand"""
        self.log.info('[+] recursively getting all data '
                      f'from { url } ')
        try:
            result = subprocess.check_output(  # nosec
                    cmd,
                    cwd=cwd,
                    stderr=stderr,
                    shell=shell
                ).decode('UTF-8').splitlines()
        except subprocess.CalledProcessError as err:
            sys.stderr.write('\n'.join([line for line in result]) + '\n')
            sys.stderr.write(str(err.output) + '\n')
            sys.exit(err.returncode)

        cmd = ['find',
               CTU_Dataset.get_fullname(name),
               '-name',
               '*?C=*',
               '-delete']
        try:
            result = subprocess.check_output(  # nosec
                    cmd,
                    cwd=cwd,
                    stderr=stderr,
                    shell=shell
                ).decode('UTF-8').splitlines()
        except subprocess.CalledProcessError as err:
            sys.stderr.write('\n'.join([line for line in result]) + '\n')
            sys.stderr.write(str(err.output) + '\n')
            sys.exit(err.returncode)


# vim: set ts=4 sw=4 tw=0 et :
