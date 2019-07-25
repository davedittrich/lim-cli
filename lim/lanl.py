# -*- coding: utf-8 -*-

import json
import logging
import os
import textwrap

from cliff.command import Command
from .main import BUFFER_SIZE
from .main import DAY
from .utils import check_whole
from .utils import safe_to_open
from .utils import BZ2_LineReader


LANL_WLS_URL_TEMPLATE = 'https://s3-us-gov-west-1.amazonaws.com/unified-host-network-dataset/2017/wls/wls_day-{day:02d}.bz2'  # noqa
LANL_NETFLOW_URL_TEMPLATE = 'https://s3-us-gov-west-1.amazonaws.com/unified-host-network-dataset/2017/netflow/netflow_day-{day:02d}.bz2'  # noqa


def netflow_filename(dataurl, datadir=''):
    datafile = os.path.join(
        datadir,
        os.path.basename(dataurl).replace('.bz2', '.csv'))
    return datafile


def wls_filenames(dataurl, datadir=''):
    base = os.path.splitext(os.path.basename(dataurl))[0]
    one_v_data = os.path.join(datadir,
                              '{}_1v.csv'.format(base))
    two_v_data = os.path.join(datadir,
                              '{}_2v.csv'.format(base))
    return one_v_data, two_v_data


def download_wls(day, datadir='', maxlines=None, force=False):
    """
    Get LANL WLS data BZ2 file, decompressing and splitting into
    single-vertex and two-vertex CSV data files.
    """
    dataurl = LANL_WLS_URL_TEMPLATE.format(day=int(day))
    one_v_data, two_v_data = wls_filenames(dataurl, datadir=datadir)
    safe_to_open(one_v_data, force)
    safe_to_open(two_v_data, force)
    single_vertex_events = [1100, 4800, 4801, 4802, 4803, 4688, 4689, 4608, 4609]  # noqa
    with open(one_v_data, 'w') as outfile_1v, open(two_v_data, 'w')\
            as outfile_2v:
        for record in BZ2_LineReader(dataurl,
                                     buffer_size=BUFFER_SIZE).readlines(
                                             maxlines=maxlines):
            j = json.loads(record)
            if int(Field(j, 'EventID', 'int')) in single_vertex_events:
                writeCSVRecord(outfile_1v, j)
            else:
                writeCSVRecord(outfile_2v, j)
    pass


def download_netflow(day, datadir='', maxlines=None, force=False):
    """
    Get LANL Netflow data BZ2 file, decompressing into
    CSV data file.
    """
    dataurl = LANL_NETFLOW_URL_TEMPLATE.format(day=int(day))
    datafile = netflow_filename(dataurl, datadir=datadir)
    safe_to_open(datafile, force)
    with open(datafile, 'wb') as fp:
        for record in BZ2_LineReader(dataurl,
                                     buffer_size=BUFFER_SIZE).readlines(
                                             maxlines=maxlines):
            fp.write(record.encode('UTF-8'))
    pass


def Field(record, fieldName, fieldType='str'):
    if fieldName in record:
        if fieldType == 'int':
            return str(int(record[fieldName]))
        elif fieldType == 'hex':
            x = int(record[fieldName], 16)
            if x & 0x8000000000000000 == 0x8000000000000000:
                x = -((x ^ 0xffffffffffffffff) + 1)
            return x
        else:
            return str(record[fieldName])
    else:
        if fieldType in ['int', 'hex']:
            return "0"
        else:
            return ""


"""
Event Record Layout

  Time, EventID, LogHost, LogonType, LogonTypeDescription, UserName,
  DomainName, LogonID, SubjectUserName, SubjectDomainName, SubjectLogonID,
  Status, Source, ServiceName, Destination, AuthenticationPackage,
  FailureReason, ProcessName, ProcessID, ParentProcessName, ParentProcessID
"""


def writeCSVRecord(fh, record):
    fh.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" % (  # noqa
          Field(record, 'Time', 'int'),
          Field(record, 'EventID', 'int'),
          Field(record, 'LogHost'),
          Field(record, 'LogonType', 'int'),
          Field(record, 'LogonTypeDescription'),
          Field(record, 'UserName'),
          Field(record, 'DomainName'),
          Field(record, 'LogonID', 'hex'),
          Field(record, 'SubjectUserName'),
          Field(record, 'SubjectDomainName'),
          Field(record, 'SubjectLogonID'),
          Field(record, 'Status'),
          Field(record, 'Source'),
          Field(record, 'ServiceName'),
          Field(record, 'Destination'),
          Field(record, 'AuthenticationPackage'),
          Field(record, 'FailureReason'),
          Field(record, 'ProcessName'),
          Field(record, 'ProcessID', 'hex'),
          Field(record, 'ParentProcessName'),
          Field(record, 'ParentProcessID', 'hex'),
          ),
    )


class LanlGet(Command):
    """Get LANL dataset for specified day(s)."""

    log = logging.getLogger(__name__)

    def get_epilog(self):
        return textwrap.dedent("""\
            For testing purposes, use ``--maxlines`` to limit the number of
            lines to read from each file.
            """)

    def get_parser(self, prog_name):
        parser = super(LanlGet, self).get_parser(prog_name)
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help="Force over-writing files if they exist (default: False)."
        )
        parser.add_argument(
            '-L', '--maxlines',
            metavar='<lines>',
            dest='maxlines',
            default=None,
            help="Maximum number of lines to get (default: None)"
        )
        parser.add_argument(
            'day',
            nargs='+',
            default=DAY,
            help="Day(s) for which to get data" +
                 "(Env: DAY; default: {})".format(DAY))
        return parser

    def take_action(self, parsed_args):
        self.log.debug('getting LANL data')
        if not os.path.exists(self.app_args.data_dir):
            os.mkdir(self.app_args.data_dir, 0o750)
        datatype = self.cmd_name.split()[-1]
        for day in parsed_args.day:
            check_whole(day)
            self.log.debug('downloading {} '.format(datatype) +
                           'data for day {}'.format(day))
            if datatype == 'netflow':
                download_netflow(day,
                                 datadir=self.app_args.data_dir,
                                 maxlines=int(parsed_args.maxlines),
                                 force=parsed_args.force)
            else:
                download_wls(day,
                             datadir=self.app_args.data_dir,
                             maxlines=int(parsed_args.maxlines),
                             force=parsed_args.force)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
