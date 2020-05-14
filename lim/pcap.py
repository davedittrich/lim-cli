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

from cliff.command import Command


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
            Adjusts the timestamps in the ethernet frame headers of packets in a PCAP
            file by rebasing them to the specified date. The ``--start-time`` is specified
            in ISO 8601 date format, e.g., ``2019-09-01T12:00:00Z`` or
            ``2019-09-01T20:00:00.00-08:00``.

            To see the old and new timestamps for each packet as they are converted,
            use ``-vv``.

            NOTE: Keep in mind that any embedded timestamps in the body of ethernet
            frames (e.g., in the UDP or TCP data portion of the packet) are not adjusted.
            """)  # noqa
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
                packet_number = 1
                for ts, buf in reader:
                    newts, newbuf = self.shift(this, ts, buf)
                    if self.app_args.verbose_level > 1:
                        if packet_number == 1:
                            logger.info('[+] details of time shift '
                                        'following with these fields:')
                            logger.info('[+] PACKET_NUMBER OLD_TIMESTAMP '
                                        'NEW_TIMESTAMP')
                        logger.info('{} {} {}'.format(packet_number,
                                                      str(arrow.get(ts)),
                                                      str(arrow.get(newts))))
                    writer.writepkt(newbuf, newts)
                    packet_number += 1


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

# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
