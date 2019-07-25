# -*- coding: utf-8 -*-

from __future__ import print_function

import ipaddress
import json
import logging
import os
import six
import time
import requests
import textwrap
import warnings

from bs4 import BeautifulSoup  # noqa
from collections import OrderedDict
from cliff.command import Command
from cliff.lister import Lister
from datetime import datetime
from urllib3.exceptions import InsecureRequestWarning
from .main import BUFFER_SIZE
from .main import DEFAULT_PROTOCOLS
from .utils import safe_to_open
from .utils import LineReader

# Initialize a logger for this module.
logger = logging.getLogger(__name__)


def unhex(x):
    """Ensure hexidecimal strings are converted to decimal form"""
    if x == '':
        return '0'
    elif x.startswith('0x'):
        return str(int(x, base=16))
    else:
        return x


# TODO(dittrich): Add support for IPv6
def IPv4ToID(x):
    """
    Convert IPv4 dotted-quad address to INT for more
    efficient use with xGT.
    """

#     try:
#         if six.PY2:
#             id = int(ipaddress.IPv4Address(x.decode('utf-8')))
#         else:
#             id = int(ipaddress.IPv4Address(x))
#     except ipaddress.AddressValueError as err:
#         if 'Expected 4 octets' in err.str:
#             logger.info(str(err))
#     return id

    if six.PY2:
        id = int(ipaddress.IPv4Address(x.decode('utf-8')))
    else:
        id = int(ipaddress.IPv4Address(x))
    return id


def download_ctu13_netflow(url=None,
                           datadir='',
                           maxlines=None,
                           protocols=['any'],
                           force=False):
    """
    Get CTU Netflow data BZ2 file, decompressing into
    CSV data file. This function also filters input by
    row and/or column to produce "clean" data for use
    by xGT without further post-load processing.

    Examples of (randomly sampled) first lines:
    Botnet 17-1:  'StartTime,Dur,Proto,SrcAddr,Sport,Dir,DstAddr,Dport,State,sTos,dTos,TotPkts,TotBytes,SrcBytes,srcUdata,dstUdata,Label\n'
    Botnet 50:    'StartTime,Dur,Proto,SrcAddr,Sport,Dir,DstAddr,Dport,State,sTos,dTos,TotPkts,TotBytes,SrcBytes,Label\n'
    Botnet 367-1: 'StartTime,Dur,Proto,SrcAddr,Sport,Dir,DstAddr,Dport,State,sTos,dTos,TotPkts,TotBytes,SrcBytes,SrcPkts,Label\n'

    """  # noqa

    infilename = url.split('/')[-1]
    outfilename = os.path.join(datadir, infilename)
    safe_to_open(outfilename, force)
    _columns = ['StartTime', 'Dur', 'Proto', 'SrcAddr', 'Sport',  # noqa
                'Dir', 'DstAddr', 'Dport', 'State', 'sTos',
                'dTos', 'TotPkts', 'TotBytes', 'SrcBytes', 'Label']
    _remove_columns = ['Dir', 'sTos', 'dTos']  # noqa
    use_columns = [0, 1, 2, 3, 4, 6, 7, 8, 11, 12, 13, 14]
    with open(outfilename, 'wb') as fp:
        # We're disabling SSL certificate verification ("verify=False")
        # in this specific case because (a) the CTU web server
        # certificate is invalid, and (b) we're only loading data
        # for test purposes. DON'T DO THIS as a general rule.
        linereader = LineReader(url,
                                verify=False,
                                buffer_size=BUFFER_SIZE)
        # header = linereader.get_header()
        # fp.write(header.encode('UTF-8') + '\n')
        count = 0
        _filter_protocols = len(protocols) > 0 or \
            (len(protocols) == 1 and 'any' in protocols)
        for record in [line.strip() for line in linereader.readlines()]:
            # Skip all lines after first (header) line that we don't want.
            fields = record.strip().split(',')
            if count > 0:
                if _filter_protocols and fields[2] not in protocols:
                    continue
                else:
                    # Convert datetimes to epoch times for faster comparisons
                    try:
                        fields[0] = str(datetime.strptime(fields[0],
                                        '%Y/%m/%d %H:%M:%S.%f').timestamp())
                    except Exception as err:  # noqa
                        pass
                    # Convert ICMP hex fields to decimal values so all ports
                    # can be inserted into xGT as INT instead of TEXT.
                    if fields[2] == 'icmp':
                        fields[4] = unhex(fields[4])
                        fields[7] = unhex(fields[7])
            # Rejoin only desired columns
            record = ','.join([fields[i] for i in use_columns]) + '\n'
            fp.write(record.encode('UTF-8'))
            count += 1
            # The CTU datasets have a header line. Make sure to not
            # count it when comparing maxlines.
            if maxlines is not None and count > int(maxlines):
                break
        logger.info('[+] wrote file {}'.format(outfilename))


class CTU13_Dataset(object):
    """
    Class for CTU13 dataset metadata.

    This class gets metadata about available labeled and unlabeled
    bi-directional NetFlow data files from the CTU-13 dataset. It does
    this by scraping the CTU web site for metadata and identifying
    the path to the file (which varies, depending on whether it
    is the unlabeled version, or the post-processed labeled
    version.

    Since it takes a long time to scrape the web site, a cache of
    collected metadata is used. If the timeout period for the cache
    has expired, the file does not exist, or the --ignore-cache
    flag is given, the site will be scraped.
    """

    __DATASETS_URL__ = 'https://mcfp.felk.cvut.cz/publicDatasets/'
    __NETFLOW_DATA_DIR__ = 'detailed-bidirectional-flow-labels/'
    __TEST_FULL_SCENARIO_URL__ = ('https://mcfp.felk.cvut.cz/publicDatasets/'
                                  'CTU-Malware-Capture-Botnet-42/')
    __TEST_FULL_NETFLOW_URL__ = ('https://mcfp.felk.cvut.cz/publicDatasets/'
                                 'CTU-Malware-Capture-Botnet-42/'
                                 'detailed-bidirectional-flow-labels/'
                                 'capture20110810.binetflow')
    __CACHE_FILE__ = "ctu13-cache.json"
    __TIMEOUT__ = 60 * 60 * 24 * 7  # secs * mins * hours * days
    __CORE_SCENARIOS__ = [str(s) for s in range(42, 59)]
    __COLUMNS__ = [
        'SCENARIO',
        'SCENARIO_URL',
        'PROBABLE_NAME',
        'DATAFILE',
        'LABELED',
        'MD5',
        'SHA1',
        'SHA256'
    ]

    def __init__(self,
                 url=__DATASETS_URL__,
                 columns=__COLUMNS__,
                 timeout=__TIMEOUT__,
                 ignore_cache=False,
                 cache_file=__CACHE_FILE__,
                 debug=False):
        """Initialize object."""

        super(CTU13_Dataset, self).__init__()
        self.url = url
        self.scenarios = OrderedDict()
        self.netflow_urls = dict()
        self.attributes = dict()
        self.columns = columns
        self.timeout = timeout
        self.ignore_cache = ignore_cache
        self.cache_file = cache_file
        self.debug = debug
        if not self.cache_expired() and not self.ignore_cache:
            self.read_cache()
        else:
            for scenario in self.get_scenarios():
                self.get_scenario_netflow_metadata(scenario)
            self.write_cache()

    def cache_expired(self, timeout=__TIMEOUT__):
        """
        Returns True if cache_file is expired or does not exist.
        Returns False if file exists and is not expired.
        """

        cache_expired = True
        now = time.time()
        try:
            stat_results = os.stat(self.cache_file)
            if stat_results.st_size == 0:
                logger.debug('[!] found empty cache')
                self.delete_cache()
            age = now - stat_results.st_mtime
            if age <= timeout:
                logger.debug('[!] cache {} '.format(self.cache_file) +
                             'has not yet expired')
                cache_expired = False
        except FileNotFoundError as err:  # noqa
            logger.debug('[!] cache {} '.format(self.cache_file) +
                         'not found')
        return cache_expired

    def read_cache(self):
        """
        Load cached data (if any). Returns True if read
        was successful, otherwise False.
        """

        _cache = dict()
        if not self.cache_expired():
            with open(self.cache_file, 'r') as infile:
                _cache = json.load(infile)
            self.url = _cache['url']
            self.attributes = _cache['attributes']
            self.scenarios = _cache['scenarios']
            self.netflow_urls = _cache['netflow_urls']
            self.columns = _cache['columns']
            logger.debug('[!] loaded metadata from cache: ' +
                         '{}'.format(self.cache_file))
            return True
        return False

    def write_cache(self):
        """Save metadata to local cache as JSON"""

        _cache = dict()
        _cache['url'] = self.url
        _cache['attributes'] = self.attributes
        _cache['scenarios'] = self.scenarios
        _cache['netflow_urls'] = self.netflow_urls
        _cache['columns'] = self.columns
        with open(self.cache_file, 'w') as outfile:
            json.dump(_cache, outfile)
        logger.debug('[!] wrote new cache file ' +
                     '{}'.format(self.cache_file))
        return True

    def delete_cache(self):
        """Delete cache file"""

        os.remove(self.cache_file)
        logger.debug('[!] deleted cache file {}'.format(self.cache_file))
        return True

    def get_scenarios(self, url=__DATASETS_URL__):
        """Scrape CTU-13 web site for metadata about binetflow
        files that are available."""

        # See "verify=False" comment in download_netflow() function.
        # See also: https://stackoverflow.com/questions/15445981/how-do-i-disable-the-security-certificate-check-in-python-requests  # noqa
        # requests.packages.urllib3.disable_warnings(
        #     category=InsecureRequestWarning)

        logger.info('[+] identifying scenarios from {}'.format(url))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            requests.packages.urllib3.disable_warnings(
                category=InsecureRequestWarning)
            response = requests.get(url, verify=False)  # nosec
        soup = BeautifulSoup(response.text, 'html.parser')
        for item in soup.findAll('a'):
            # href = item['href']
            # if href.endswith('.binetflow') \
            #    or href.endswith('.netflow.csv'):
            #     scenarios[url] = href
            #     break
            try:
                href = item['href']
            except KeyError:
                href = ''
            lower_str = str(href).lower()
            try:
                find_str = 'ctu-malware-capture-botnet-'
                loc = lower_str.index(find_str)
                name = href[loc+len(find_str):].strip('/')
                if self.debug and name not in self.__CORE_SCENARIOS__:
                    continue
                self.scenarios[name] = url + href
            except ValueError:
                pass
        for k, v in self.scenarios.items():
            if k not in self.attributes:
                # Populate attribute dictionary for this scenario
                self.attributes[k] = dict()
                self.attributes[k]['SCENARIO'] = k.strip()
                self.attributes[k]['SCENARIO_URL'] = v.strip()
                for c in self.columns:
                    # ... including as-yet-undefined attributes
                    if c not in self.attributes[k]:
                        self.attributes[k][c] = ''
        return self.scenarios.keys()

    def get_scenario_netflow_metadata(self, scenario=None):
        """
        Get metadata for CTU-13 scenario dataset

        This function attempts to find a README.md file documenting
        the contents of the directory, extracting from it the metadata
        attributes desired for our purposes.
        """

        if scenario is None:
            raise RuntimeError('no scenario given')

        # See "verify=False" comment in download_netflow() function.
        # See also: https://stackoverflow.com/questions/15445981/how-do-i-disable-the-security-certificate-check-in-python-requests  # noqa
        # requests.packages.urllib3.disable_warnings(
        #     category=InsecureRequestWarning)

        try:
            scenario_url = self.scenarios[scenario]
        except KeyError:
            raise RuntimeError('scenario {} was not found'.format(scenario))

        # Prefer the fully-labeled file, but fall back if not available.
        readme_url = scenario_url + 'README.md'
        netflow_sources = [
            "{}{}".format(scenario_url, self.__NETFLOW_DATA_DIR__),
            scenario_url
        ]
        for source in netflow_sources:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                requests.packages.urllib3.disable_warnings(
                    category=InsecureRequestWarning)
                response = requests.get(source, verify=False)  # nosec
            # if response.status_code in [404] or (scenario in self.netflow_urls):  # noqa
            if response.status_code in [404]:  # noqa
                continue

            # File was found. Parse it, line by line, looking for
            # path to NetFlow .csv file in top level directory.
            soup = BeautifulSoup(response.text, 'html.parser')
            # Example full URL:
            # https://mcfp.felk.cvut.cz/publicDatasets/CTU-Malware-Capture-Botnet-42/detailed-bidirectional-flow-labels/capture20110810.binetflow  # noqa
            for item in soup.findAll('a'):
                href = item['href']
                netflow_url = str(source + href)
                if href.startswith('?') or \
                   href.startswith('http://') or \
                   href.startswith('https://') or \
                   href.startswith('/publicDatasets/'):
                    logger.debug('[!] ignoring href {}'.format(href))
                    continue
                if href.endswith('.binetflow') or \
                   href.endswith('.netflow.csv'):
                    if scenario in self.netflow_urls:
                        logger.info('[-] passing alternative netflow ' +
                                    '{} '.format(netflow_url))
                    else:
                        logger.info('[+] found netflow file ' +
                                    '{}'.format(netflow_url))
                        self.netflow_urls[scenario] = netflow_url
                        self.attributes[scenario]['DATAFILE'] = href
                        self.attributes[scenario]['LABELED'] =\
                            self.__NETFLOW_DATA_DIR__ in netflow_url

        # Now get remainder of metadata from README.md
        response = requests.get(readme_url, verify=False)  # nosec
        if response.status_code not in [404]:
            for line in response.content.decode('utf-8').split('\n'):
                if line.startswith('- '):
                    try:
                        field, value = line[2:].split(': ')
                        field = field.upper().replace(' ', '_')
                        if field in self.columns:
                            self.attributes[scenario][field] = value.strip()
                    except ValueError as err:  # noqa
                        pass

    def get_netflow_url(self, scenario=None):
        """Return the URL for the NetFlow file for scenario."""
        if scenario not in self.netflow_urls:
            raise RuntimeError(('no NetFlow file for scenario '
                                '{}'.format(scenario)))
        return self.netflow_urls[scenario]

    def get_metadata(self, name_includes=None, has_hash=None):
        """
        Return a list of lists of data suitable for use by
        cliff, following the order of elements in self.columns.
        """
        data = list()
        for k, v in self.attributes.items():
            scenario = self.attributes[k]
            if scenario['DATAFILE'] != '':
                if name_includes is not None:
                    if name_includes.lower() not in scenario['PROBABLE_NAME'].lower():  # noqa
                        continue
                if has_hash is not None:
                    if not (has_hash == scenario['MD5'] or
                            has_hash == scenario['SHA1'] or
                            has_hash == scenario['SHA256']):
                        continue
                data.append([scenario[c] for c in self.columns])
        return data


class CTU13Get(Command):
    """Get CTU-13 dataset."""

    log = logging.getLogger(__name__)

    def get_epilog(self):
        return textwrap.dedent("""\
            For testing purposes, use --maxlines to limit the number of
            lines to read from each file.
            """)

    def get_parser(self, prog_name):
        parser = super(CTU13Get, self).get_parser(prog_name)
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help="Force over-writing files if they exist (default: False)."
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
        parser.add_argument(
            '--ignore-cache',
            action='store_true',
            dest='ignore_cache',
            default=False,
            help="Ignore any cached results (default: False)."
        )
        parser.add_argument('scenario', nargs='*', default=[])
        return parser

    def take_action(self, parsed_args):
        self.log.debug('[!] getting CTU data')
        if 'ctu13_dataset' not in dir(self):
            self.ctu13_dataset = CTU13_Dataset(
                ignore_cache=parsed_args.ignore_cache,
                debug=self.app_args.debug)

        if not os.path.exists(self.app_args.data_dir):
            os.mkdir(self.app_args.data_dir, 0o750)
        datatype = self.cmd_name.split()[-1]
        if len(parsed_args.scenario) == 0:
            raise RuntimeError(('must specify a scenario: '
                                'try "lim ctu13 list netflow"'))
        self.log.debug('[!] downloading ctu-13 {} data'.format(datatype))

        for scenario in parsed_args.scenario:
            if datatype == 'netflow':
                download_ctu13_netflow(
                    url=self.ctu13_dataset.get_netflow_url(scenario),
                    datadir=self.app_args.data_dir,
                    protocols=parsed_args.protocols,
                    maxlines=parsed_args.maxlines,
                    force=parsed_args.force)
            else:
                raise RuntimeError('getting "{}" '.format(datatype) +
                                   'not implemented')


class CTU13List(Lister):
    """List CTU-13 Botnet data metadata."""

    log = logging.getLogger(__name__)

    def get_epilog(self):
        return textwrap.dedent("""\
            """)

    def get_parser(self, prog_name):
        parser = super(CTU13List, self).get_parser(prog_name)
        parser.add_argument(
            '--ignore-cache',
            action='store_true',
            dest='ignore_cache',
            default=False,
            help="Ignore any cached results (default: False)."
        )
        find = parser.add_mutually_exclusive_group(required=False)
        find.add_argument(
            '--hash',
            dest='hash',
            metavar='<{md5|sha1|sha256} hash>',
            default=None,
            help=('Only list scenarios that involve a '
                  'specific hash (default: None).')
        )
        find.add_argument(
            '--name-includes',
            dest='name_includes',
            metavar='<string>',
            default=None,
            help=('Only list "PROBABLE_NAME" including this '
                  'string (default: None).')
        )
        return parser

    # FYI, https://mcfp.felk.cvut.cz/publicDatasets/CTU-Malware-Capture-Botnet-269-1/README.html  # noqa
    # is an Emotet sample...
    # TODO(dittrich): Figure out how to handle these

    def take_action(self, parsed_args):
        self.log.debug('[!] listing CTU data')
        if 'ctu13_dataset' not in dir(self):
            self.ctu13_dataset = CTU13_Dataset(
                ignore_cache=parsed_args.ignore_cache,
                debug=self.app_args.debug)
        columns = self.ctu13_dataset.columns
        data = self.ctu13_dataset.get_metadata(
            name_includes=parsed_args.name_includes,
            has_hash=parsed_args.hash)
        return columns, data


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
