# -*- coding: utf-8 -*-

from __future__ import print_function

import argparse
import arrow
import dpkt
import logging
import os
import socket
import sys
import textwrap
import warnings

from arrow.factory import ArrowParseWarning
from cliff.command import Command

# Ignore parse warning per
# https://github.com/crsmithdev/arrow/issues/612
warnings.simplefilter("ignore", ArrowParseWarning)

# TODO(dittrich): Make this a command line argument?
# Initialize a logger for this module.
logger = logging.getLogger(__name__)


class PCAPShift(Command):
    """Shift timestamps or source/destination addresses in PCAP files."""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(PCAPShift, self).get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            'pcap',
            nargs='*',
            default=None)
        parser.add_argument(
            '--start-time',
            action='store',
            dest='start_time',
            default=None,
            help="New starting time for first packet (default: None)."
        )
        parser.epilog = textwrap.dedent("""
            Adjust attributes in a PCAP file, such as rebasing the timestamps.
            """)
        return parser

    def networkshift(self, ts, buf):
        raise RuntimeError('Not implemented')
        return ts, buf

    def timeshift(self, ts, buf):
        """Adjust timestamps."""
        newts = ts
        if self.start_time is not None:
            # Calculate the delta from the first packet.
            if self.time_delta is None:
                ats = arrow.get(ts)
                self.time_delta = self.start_time - ats.float_timestamp
                logger.debug('[+] first packet time is {} '.format(ats) +
                             '({})'.format(ats.float_timestamp))
                logger.debug('[+] time delta is {}'.format(self.time_delta))
                newats = arrow.get(ts + self.time_delta)
                logger.debug('[+] new first packet time is ' +
                             '{} '.format(newats) +
                             '({})'.format(newats.float_timestamp))
            newts = ts + self.time_delta
        return newts, buf

    def shift(self, this, ts, buf):
        """Simulated case statement."""
        options = {
            'network': self.networkshift,
            'time': self.timeshift,
        }
        if this in options:
            func = options.get(this, lambda: None)
            if func is not None:
                return func(ts, buf)
            else:
                raise RuntimeError('Shifting "{}" '.format(this) +
                                   'is not implemented')

    def take_action(self, parsed_args):
        this = self.cmd_name.split()[-1]
        self.log.debug('[+] shifting {} '.format(this) +
                       'in PCAP file(s)')

        self.start_time = None
        self.time_delta = None

        # Process options before delegating to subfunction.
        if parsed_args.start_time is not None:
            self.start_time = arrow.get(
                parsed_args.start_time).float_timestamp
            logger.debug('[+] start_time is '
                         '{} '.format(parsed_args.start_time) +
                         '({})'.format(self.start_time))

        # Iterate over all file arguments, delegating to subfunction based on
        # the subcommand string using a 'case' like delegator.
        for fname in parsed_args.pcap:
            logger.debug('[+] original pcap file: {}'.format(fname))
            newfname = '{}-{}-shifted.pcap'.format(os.path.splitext(fname)[0],
                                                   this)
            logger.debug('[+] new pcap file: {}'.format(newfname))
            if not os.path.exists(fname):
                raise RuntimeError('PCAP file {} does not exist'.format(fname))
            with open(fname, 'rb') as f_in, open(newfname, 'wb') as f_out:
                reader = dpkt.pcap.Reader(f_in)
                writer = dpkt.pcap.Writer(f_out)
                for ts, buf in reader:
                    newts, newbuf = self.shift(this, ts, buf)
                    writer.writepkt(newbuf, newts)


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
            """)
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

# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
