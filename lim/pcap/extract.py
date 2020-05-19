# -*- coding: utf-8 -*-

from __future__ import print_function

import argparse
import dpkt
import logging
import os
import socket
import sys
import textwrap

from cliff.command import Command


# TODO(dittrich): Make this a command line argument?
# Initialize a logger for this module.
logger = logging.getLogger(__name__)


class PCAPExtract(Command):
    """Extract source and destination IP addresses from PCAP file(s)."""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(PCAPExtract, self).get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            'pcap',
            nargs='*',
            default=None)
        parser.add_argument(
            '--stdout',
            action='store_true',
            dest='stdout',
            default=False,
            help="Write output to stdout (default: False)."
        )
        parser.epilog = textwrap.dedent("""
            Output is a sorted list of unique IP addresses. By default, the results are
            written to a file with the same base name as the input, but ending
            in ``.ips``. To output to standard output, use the ``--stdout`` option.
            """)  # noqa
        return parser

    def take_action(self, parsed_args):
        self.log.debug('[+] extracting IP addresses')
        for fname in parsed_args.pcap:
            if parsed_args.stdout:
                f_out = sys.stdout
            else:
                flist = os.path.splitext(fname)[0] + '.ips'
                f_out = open(flist, 'w')
                logger.debug('[+] writing IP addresses ' +
                             'to file: {}'.format(flist))
            with open(fname, 'rb') as f_in:
                reader = dpkt.pcap.Reader(f_in)
                ips = dict()
                for ts, buf in reader:
                    eth = dpkt.ethernet.Ethernet(buf)
                    if isinstance(eth.data, dpkt.ip.IP):
                        ip = eth.data
                        src = socket.inet_ntop(socket.AF_INET, ip.src)
                        dst = socket.inet_ntop(socket.AF_INET, ip.dst)
                    ips[src] = True
                    ips[dst] = True
                for ip in sorted(ips.keys(),
                                 key=lambda item: socket.inet_aton(item)):
                    f_out.write('{}\n'.format(ip))
            if not parsed_args.stdout:
                f_out.close()


# vim: set ts=4 sw=4 tw=0 et :
