# -*- coding: utf-8 -*-

import aiohttp
import async_timeout
import asyncio
import ipaddress
import json
import logging
import os
import requests
import signal
import six
import textwrap
import time
import warnings

from bs4 import BeautifulSoup
from collections import OrderedDict
from datetime import datetime
from lim import BUFFER_SIZE
from lim.utils import safe_to_open
from lim.utils import LineReader
from urllib3.exceptions import InsecureRequestWarning

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
    Convert IPv4 dotted-quad address to INT.
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


def download_ctu_netflow(url=None,
                         datadir='',
                         maxlines=None,
                         protocols=['any'],
                         force=False):
    """
    Get CTU Netflow data BZ2 file, decompressing into
    CSV data file. This function also filters input by
    row and/or column to produce "clean" data for use
    without further post-load processing.

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
                    # can be inserted into tables as INT instead of TEXT.
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


class CTU_Dataset(object):
    """
    Class for CTU dataset metadata.

    This class gets metadata about available CTU datasets.  It does
    this by scraping the CTU web site for metadata and identifying
    the path to the file (which varies, depending on whether it
    is the unlabeled version, or the post-processed labeled
    version. Scraped data is cached for a period of time. You can
    force re-loading by using the --ignore-cache flag.


    Examples of URLs from each set (for the purpose of knowing how
    to parse them):

    https://mcfp.felk.cvut.cz/publicDatasets/CTU-Malware-Capture-Botnet-9/
    https://mcfp.felk.cvut.cz/publicDatasets/CTU-Normal-7/
    https://mcfp.felk.cvut.cz/publicDatasets/CTU-Mixed-Capture-4/
    https://mcfp.felk.cvut.cz/publicDatasets/IoTDatasets/CTU-IoT-Malware-Capture-34-1/

    Note that the IoT datasets have a different directory path than
    the rest, which complicates URL parsing logic below.
    """

    __CTU_DATASETS_OVERVIEW_URL__ = \
        'https://www.stratosphereips.org/datasets-overview'
    __ASYNC_TIMEOUT__ = 10
    __SEMAPHORE_LIMIT__ = 10
    # The "CTU13" datasets are just 13 special datasets out of the
    # 'malware' group here. They will have bidirectional labelled
    # network flows ('BINETFLOW') in a subdirectory specified by
    # __NETFLOW_DATA_DIR__.
    # https://mcfp.felk.cvut.cz/publicDatasets/
    __CTU_DATASET_GROUPS__ = {
        'mixed': 'https://www.stratosphereips.org/datasets-mixed',
        'normal': 'https://www.stratosphereips.org/datasets-normal',
        'malware': 'https://www.stratosphereips.org/datasets-malware',
        'iot': 'https://www.stratosphereips.org/datasets-iot',
    }
    __CTU_PREFIX__ = 'CTU-Malware-Capture-'
    __DEFAULT_GROUP__ = 'malware'
    __DATASETS_URL__ = __CTU_DATASET_GROUPS__[__DEFAULT_GROUP__]
    __NETFLOW_DATA_DIR__ = 'detailed-bidirectional-flow-labels/'
    # Put the cache file in user's home directory by default
    # (or fall back to cwd, just to be robust).
    __CACHE_FILE__ = os.environ.get(
        'LIM_CTU_CACHE',
        os.path.join(os.getenv('HOME', os.getcwd()),
                     '.lim-ctu-cache.json')
        )
    __CACHE_TIMEOUT__ = 60 * 60 * 24 * 30  # secs * mins * hours * days
    # These are fields associated with files that can be downloaded.
    __ATTRIBUTES__ = [
        'ZIP',
        'LABELED',
        'BINETFLOW',
        'PCAP',
    ]
    # These are all columns, in the order we want them to occur in output
    # (including __ARTIFACT__ fields just defined.)
    __COLUMNS__ = [
        'SCENARIO',
        'GROUP',
        'PROBABLE_NAME',
        'SCENARIO_URL',
        'ZIP',
        'MD5',
        'SHA1',
        'SHA256',
        'LABELED',
        'BINETFLOW',
        'PCAP',
        'WEBLOGNG'
    ]
    __MIN_COLUMNS__ = 4
    __DISCLAIMER__ = textwrap.dedent("""\
       When using this data, make sure to respect the Disclaimer at the bottom of
       the scenario ``Readme.*`` files:

       .. code-block:: console

          These files were generated in the Stratosphere Lab as part of the Malware
          Capture Facility Project in the CVUT University, Prague, Czech Republic.
          The goal is to store long-lived real botnet traffic and to generate labeled
          netflows files.

          Any question feel free to contact us:
          Sebastian Garcia: sebastian.garcia@agents.fel.cvut.cz

          You are free to use these files as long as you reference this project and
          the authors as follows:

          Garcia, Sebastian. Malware Capture Facility Project. Retrieved
          from https://stratosphereips.org

       ..

       To cite the [CTU13] dataset please cite the paper "An empirical comparison of
       botnet detection methods" Sebastian Garcia, Martin Grill, Jan Stiborek and Alejandro
       Zunino. Computers and Security Journal, Elsevier. 2014. Vol 45, pp 100-123.
       http://dx.doi.org/10.1016/j.cose.2014.05.011

    """)  # noqa

    def __init__(self,
                 cache_timeout=__CACHE_TIMEOUT__,
                 async_timeout=__ASYNC_TIMEOUT__,
                 semaphore_limit=__SEMAPHORE_LIMIT__,
                 cache_file=None,
                 ignore_cache=False,
                 debug=False):
        """Initialize object."""

        self.cache_timeout = cache_timeout
        self.semaphore_limit = semaphore_limit
        self.async_timeout = async_timeout
        self.cache_file = \
            cache_file if cache_file is not None else self.__CACHE_FILE__
        self.ignore_cache = ignore_cache
        self.debug = debug

        # Attributes
        self.cache_expired = None
        self.scenarios = OrderedDict()
        self.columns = self.get_columns()
        self.groups = self.get_groups()
        pass

    @classmethod
    def get_cache_file(cls):
        """Return path to CTU cache file."""
        try:
            return cls.cache_file
        except AttributeError:
            return cls.__CACHE_FILE__

    @classmethod
    def get_ctu_datasets_overview_url(cls):
        """Return URL for CTU Datasets Overview web page"""
        return cls.__CTU_DATASETS_OVERVIEW_URL__

    @classmethod
    def get_groups(cls):
        """Return list of valid group names"""
        return [g for g in cls.__CTU_DATASET_GROUPS__.keys()]

    @classmethod
    def get_attributes(cls):
        """Return list of dataset attributes"""
        return [a for a in cls.__ATTRIBUTES__]

    @classmethod
    def get_attributes_lower(cls):
        """Return list of lowercase dataset attributes"""
        return [a.lower() for a in cls.__ATTRIBUTES__]

    @classmethod
    def get_url_for_group(cls, group):
        """Return URL for group"""
        return cls.__CTU_DATASET_GROUPS__.get(group)

    @classmethod
    def get_default_group(cls):
        """Returns default group name"""
        return cls.__DEFAULT_GROUP__

    @classmethod
    def get_columns(cls):
        """Returns list of columns"""
        return cls.__COLUMNS__

    @classmethod
    def get_disclaimer(cls):
        """Returns CTU disclaimer"""
        return cls.__DISCLAIMER__

    @classmethod
    def get_fullname(cls, name):
        """
        Return a full scenario name from a possible abbreviated
        name consisting of just the part after '{}'.
        """.format(cls.__CTU_PREFIX__)

        if len(name) > len(cls.__CTU_PREFIX__):
            # Don't try to add the prefix if it looks like it might already
            # be there (even typod)
            if name[0] == 'C':
                return name
        else:
            if name[0] != 'C' and not name.startswith(cls.__CTU_PREFIX__):
                return cls.__CTU_PREFIX__ + name
        return name

    @classmethod
    def get_shortname(cls, name):
        """
        Return a short scenario name from a full scenario name if
        the name begins with '{}'.
        """.format(cls.__CTU_PREFIX__)

        if name.startswith(cls.__CTU_PREFIX__):
            return name[len(cls.__CTU_PREFIX__):]
        return name

    @classmethod
    def filename_from_url(cls, url=None):
        if url is None:
            return None
        filename = url.split('/').pop()
        if filename in ['', None]:
            raise RuntimeError(
                '[-] cannot determine filename from url {}'.format(url))
        return filename

    def get_scenarios(self):
        """Returns CTU dataset scenarios"""
        return self.scenarios

    def get_scenario_names(self):
        """Returns CTU dataset scenario names"""
        return [s for s in self.scenarios.keys()]

    def is_valid_scenario(self, name):
        """Returns boolean indicating existence of scenario"""
        if type(name) is not str:
            raise RuntimeError('[-] "{}" must be type(str)'.format(name))
        return name in self.scenarios

    def get_scenario(self, name):
        """Returns CTU dataset scenario"""
        return self.scenarios.get(name)

    def get_scenario_page(self, name):
        """Returns CTU dataset scenario HTML page"""
        try:
            return self.scenarios[name].get('_PAGE')
        except Exception as err:  # noqa
            return None

    def get_scenario_attribute(self, name, attribute):
        """
        Returns CTU scenario dataset attribute.

        Discrete attributes are returned as they are.

        Compound attributes (i.e., files) are composed of the
        base URL plus the attribute's name (which may include path
        information).
        """
        if name not in self.scenarios:
            return None
        attribute = attribute.upper()
        attributes = self.get_attributes()
        if attribute in ['GROUP', 'URL']:
            try:
                result = self.scenarios[name].get(attribute)
            except Exception as err:  # noqa
                result = None
        elif attribute in attributes:
            try:
                url = self.scenarios[name]['URL']
                result = url + self.scenarios[name].get(attribute)
            except Exception as err:  # noqa
                result = None
        else:
            raise RuntimeError(
                f'[-] getting attribute "{ attribute }" is not supported')
        return result

    def fetch_scenario_content_byurl(self,
                                     url,
                                     filename=None):
        data_dir = os.path.split(filename)[0]
        if not os.path.exists(data_dir):
            os.mkdir(data_dir, 0o750)
        with open(filename, 'wb') as f:
            response = self.immediate_fetch(url)
            f.write(response.content)

    def fetch_scenario_content_byattribute(self,
                                           data_dir=None,
                                           name=None,
                                           attribute=None,
                                           filename=None):
        name = CTU_Dataset.get_fullname(name)
        url = self.get_scenario_attribute(name, attribute)
        if url in ['', None]:
            logger.info('[-] scenario "{}" does not have '.format(name) +
                        '"{}" data: skipping'.format(attribute))
        else:
            # 'https://mcfp.felk.cvut.cz/publicDatasets/CTU-Mixed-Capture-1/2015-07-28_mixed.pcap'
            if filename is None:
                filename = self.filename_from_url(url)
                # '2015-07-28_mixed.pcap'
            full_path = os.path.join(data_dir, filename)
            self.fetch_scenario_content_byurl(url, filename=full_path)

    # https://pawelmhm.github.io/asyncio/python/aiohttp/2016/04/22/asyncio-aiohttp.html

    def load_ctu_metadata(self):
        if not self.cache_has_expired() and not self.ignore_cache:
            self.read_cache()
        else:
            loop = asyncio.get_event_loop()
            loop.add_signal_handler(signal.SIGINT, loop.stop)
            future = asyncio.ensure_future(self.run_fetch())
            loop.run_until_complete(future)
            self.write_cache()

    async def record_scenario_metadata(self, semaphore, group, url, session):
        if url is None:
            raise RuntimeError('[-] url must not be None')
        if url.find('publicDatasets') == -1:
            raise RuntimeError('[-] url does not contain "publicDatasets"')
        # The scenario name is the directory name in which the file
        # is located.
        name = os.path.basename(os.path.dirname(url))
        if name not in self.scenarios:
            self.scenarios[name] = dict()
        _scenario = self.scenarios[name]
        _scenario['GROUP'] = group
        _scenario['URL'] = url
        page = await self.fetch_page(semaphore, url, session)
        # Underscore on _page means ignore later (logic coupling)
        _scenario['_PAGE'] = page
        _scenario['_SUCCESS'] = page not in ["", None] \
            and "Not Found" not in page
        if _scenario['_SUCCESS']:
            # Process links
            soup = BeautifulSoup(page, 'html.parser')
            # Scrape page for metadata
            for line in soup.text.splitlines():
                if self.__NETFLOW_DATA_DIR__ in line:
                    # TODO(dittrich): Parse subpage to get labeled binetflow
                    subpage = await self.fetch(
                        url + self.__NETFLOW_DATA_DIR__,
                        session)
                    subsoup = BeautifulSoup(subpage, 'html.parser')
                    for item in subsoup.findAll('a'):
                        if item['href'].endswith('.binetflow'):
                            _scenario['BINETFLOW'] = \
                                self.__NETFLOW_DATA_DIR__ + item['href']
                            break
                if ":" in line and line != ":":
                    try:
                        # Special case for IoT malware, which is annotated
                        # differently.
                        (_k, _v) = line.split(':')
                        k = _k.upper().replace(' ', '_')
                        if k == "PROBABLE_MALWARE_NAME":
                            k = "PROBABLE_NAME"
                        v = _v.strip()
                        if k in self.columns:
                            _scenario[k] = v
                    except (ValueError, TypeError) as err: # noqa
                        pass
                    except Exception as err:  # noqa
                        pass
            for item in soup.findAll('a'):
                try:
                    href = item['href']
                except KeyError:
                    href = ''
                if href.startswith('?'):
                    continue
                href_ext = os.path.splitext(href)[-1][1:].upper()
                if href_ext == '':
                    continue
                if href_ext in self.columns:
                    _scenario[href_ext] = href
        pass

    async def run_fetch(self):
        tasks = []
        semaphore = asyncio.Semaphore(self.semaphore_limit)
        try:
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(verify_ssl=False)) as session:  # noqa
                for group in CTU_Dataset.get_groups():
                    scenarios = self.get_scenarios_for_group(group)
                    for url in scenarios:
                        task = asyncio.ensure_future(
                            self.record_scenario_metadata(
                                semaphore, group, url, session))
                        tasks.append(task)
                responses = asyncio.gather(*tasks)
                logger.info('[+] queued {} pages '.format(len(tasks)) +
                            'for processing')
                await responses
        except KeyboardInterrupt:
            session.close()

    async def fetch_page(self, semaphore, url, session):
        """Fetch a page"""
        if self.debug:
            logger.debug('[+] fetch_page({})'.format(url))
        page = await self.bound_fetch(semaphore, url, session)
        return page.decode("utf-8")

    async def bound_fetch(self, semaphore, url, session):
        """Fetch a page asynchronously with semaphore limiting"""
        async with semaphore:
            return await self.fetch(url, session)

    async def fetch(self, url, session):
        """GET a URL asynchronously"""
        with async_timeout.timeout(self.async_timeout):
            logger.debug('[+] fetch({})'.format(url))
            async with session.get(url) as response:
                return await response.read()

    def immediate_fetch(self, url):
        """GET a page synchronously"""
        if self.debug:
            logger.debug('[+] immediate_fetch({})'.format(url))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            requests.packages.urllib3.disable_warnings(
                category=InsecureRequestWarning)
            response = requests.get(url, verify=False)  # nosec
        return response

    def cache_has_expired(self, cache_timeout=__CACHE_TIMEOUT__):
        """
        Returns True if cache_file is expired or does not exist.
        Returns False if file exists and is not expired.

        For testing, also considers a cache file that starts with
        'test-' as never being expired.
        """

        if self.cache_file.startswith('test'):
            self.cache_expired = False
        if self.cache_expired is not None:
            return self.cache_expired
        cache_expired = True
        now = time.time()
        try:
            stat_results = os.stat(self.cache_file)
            if stat_results.st_size == 0:
                logger.debug('[!] found empty cache')
                self.delete_cache()
            age = now - stat_results.st_mtime
            if age <= cache_timeout:
                logger.debug('[+] cache {} '.format(self.cache_file) +
                             'has not yet expired')
                cache_expired = False
            else:
                logger.debug('[+] cache {} '.format(self.cache_file) +
                             'has expired')
        except FileNotFoundError as err:  # noqa
            logger.debug('[+] cache {} '.format(self.cache_file) +
                         'not found')
        self.cache_expired = cache_expired
        return self.cache_expired

    def read_cache(self):
        """
        Load cached data (if any). Returns True if read
        was successful, otherwise False.
        """

        _cache = dict()
        if not self.cache_has_expired():
            with open(self.cache_file, 'r') as infile:
                _cache = json.load(infile)
            self.scenarios = _cache['scenarios']
            self.columns = _cache['columns']
            logger.debug('[+] loaded metadata from cache: ' +
                         '{}'.format(self.cache_file))
            return True
        return False

    def write_cache(self):
        """Save metadata to local cache as JSON"""

        _cache = dict()
        _cache['scenarios'] = self.scenarios
        _cache['columns'] = self.columns
        with open(self.cache_file, 'w') as outfile:
            json.dump(_cache, outfile)
        logger.debug('[+] wrote new cache file ' +
                     '{}'.format(self.cache_file))
        return True

    def delete_cache(self):
        """Delete cache file"""

        os.remove(self.cache_file)
        logger.debug('[+] deleted cache file {}'.format(self.cache_file))
        return True

    def get_scenarios_for_group(self, group=None):
        """Scrape CTU web site for metadata about binetflow
        files that are available."""

        # See "verify=False" comment in download_netflow() function.
        # See also: https://stackoverflow.com/questions/15445981/how-do-i-disable-the-security-certificate-check-in-python-requests  # noqa
        # requests.packages.urllib3.disable_warnings(
        #     category=InsecureRequestWarning)

        if group is None:
            raise RuntimeError('[-] no group name provided')
        url = CTU_Dataset.get_url_for_group(group)
        logger.info('[+] identifying scenarios for ' +
                    'group {} from {}'.format(group, url))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            requests.packages.urllib3.disable_warnings(
                category=InsecureRequestWarning)
            response = requests.get(url, verify=False)  # nosec
        soup = BeautifulSoup(response.text, 'html.parser')
        scenarios = []
        for item in soup.findAll('a'):
            try:
                href = item['href']
            except KeyError:
                href = ''
            if href.startswith('?'):
                continue
            if '/publicDatasets/' in href and href.endswith('/'):
                logger.debug('[+] found scenario {}'.format(href))
                scenarios.append(href)
        logger.info('[+] group "{}" '.format(group) +
                    'has {} scenarios'.format(len(scenarios)))
        return scenarios

    def get_metadata(self,
                     groups=None,
                     columns=None,
                     name_includes=None,
                     fullnames=False,
                     description_includes=None,
                     has_hash=None):
        """
        Return a list of lists of data suitable for use by
        cliff, following the order of elements in 'columns'.
        """
        data = []
        if groups is None:
            groups = self.groups
        for (scenario, attributes) in self.scenarios.items():
            if '_SUCCESS' in attributes and not attributes['_SUCCESS']:
                continue
            if 'GROUP' in attributes and attributes['GROUP'] not in groups:
                continue
            match = True
            if name_includes is not None:
                # Can't look for something that doesn't exist.
                if 'PROBABLE_NAME' not in attributes:
                    continue
                probable_name = attributes['PROBABLE_NAME'].lower()
                find = probable_name.find(name_includes.lower())
                match = match and (find != -1)
            elif description_includes is not None:
                # Can't look for something that doesn't exist.
                if '_PAGE' not in attributes:
                    continue
                page = attributes['_PAGE'].lower()
                find = page.find(description_includes.lower())
                match = match and (find != -1)
            if has_hash is not None:
                match = match and (has_hash == attributes.get('MD5', '') or
                                   has_hash == attributes.get('SHA1', '') or
                                   has_hash == attributes.get('SHA256', ''))
            if not match:
                continue
            row = dict()
            # Support short names for Malware scenarios.
            if fullnames:
                row['SCENARIO'] = scenario
            else:
                row['SCENARIO'] = CTU_Dataset.get_shortname(scenario)
            row['SCENARIO_URL'] = attributes['URL']
            # Get remaining attributes
            for c in columns:
                if c not in row:
                    row[c] = attributes.get(c)
            data.append([row.get(c) for c in columns])
        return data


all = [
    unhex,
    IPv4ToID,
    download_ctu_netflow,
    CTU_Dataset,
]


# vim: set ts=4 sw=4 tw=0 et :
