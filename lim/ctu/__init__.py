# -*- coding: utf-8 -*-

import aiohttp
import arrow
import async_timeout
import asyncio
import email.utils
import ipaddress
import json
import logging
import os
import re
import requests
import signal
import six
import sys
import textwrap
import time
import warnings

from bs4 import BeautifulSoup
from datetime import datetime
from lim import BUFFER_SIZE
from lim.utils import (
    safe_to_open,
    LineReader,
)
from urllib3.exceptions import InsecureRequestWarning

logger = logging.getLogger(__name__)


def date_ge(date=None, starting=None):
    """Compare date with lower bound of a range."""
    if date is None:
        return False
    if starting is None:
        return True
    return arrow.get(date) >= arrow.get(starting)


def date_le(date=None, ending=None):
    """Compare date with upper bound of a range."""
    if date is None:
        return False
    if ending is None:
        return True
    return arrow.get(date) <= arrow.get(ending)


def httpdate_to_timestamp(date_time):
    """Convert an HTTP format date string to a Unix epoch timestamp.
    """

    time_tuple = email.utils.parsedate_tz(date_time)
    return 0 if time_tuple is None else email.utils.mktime_tz(time_tuple)


def timestamp_to_httpdate(timestamp):
    """Convert a Unix epoch timestamp to an HTTP format date string.
    """

    return email.utils.formatdate(timeval=timestamp,
                                  localtime=False,
                                  usegmt=True)


def get_url_last_modified(url=None):
    if url is None:
        raise RuntimeError("[-] no 'url' specified")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        requests.packages.urllib3.disable_warnings(
            category=InsecureRequestWarning)
        response = requests.head(url, verify=False)  # nosec
    return httpdate_to_timestamp(response.headers['Last-Modified'])


def get_file_last_mtime(file_path=None, clean=True):
    """Return the last modified time of a file.

    Args:
        file_path (str): Absolute path to file
        clean (bool): Delete file if empty

    Returns:
        Last modified timestamp in Unix epoch time or
        0 if file does not exist.
    """

    if file_path is None:
        raise RuntimeError("[-] the 'file_path' argument is required")
    if os.path.abspath(file_path) != file_path:
        raise RuntimeError("[-] 'file_path' must be an absolute path")
    last_mtime = 0
    try:
        stat_results = os.stat(file_path)
        if stat_results.st_size == 0 and clean:
            logger.debug(
                f"[!] removing empty file '{file_path}'")
            os.remove(file_path)
        else:
            last_mtime = int(stat_results.st_mtime)
    except FileNotFoundError as err:  # noqa
        pass
    return last_mtime


def get_if_newer(url=None, timestamp=None):
    """GET a page if last modified after a specified time.
    """

    last_mtime = timestamp_to_httpdate(timestamp)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # Bypass warning about certificate failure
        requests.packages.urllib3.disable_warnings(
            category=InsecureRequestWarning)
        response = requests.get(
            url,
            headers={'If-Modified-Since': last_mtime},
            verify=False)  # nosec
    return response.text


def normalize_ctu_name(name):
    """Ensure name is in the normal CTU form."""
    return name.title().replace('Ctu', 'CTU').replace('Iot', 'IoT')


def unhex(x):
    """Ensure hexidecimal strings are converted to decimal form."""
    if x == '':
        return '0'
    elif x.startswith('0x'):
        return str(int(x, base=16))
    else:
        return x


def unique_iter(iterable):
    """Return only the unique items from an iterable."""
    seen = set()
    for item in iterable:
        if item in seen:
            continue
        seen.add(item)
        yield item


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

    Examples of (randomly sampled) first lines
    Botnet 17-1:  'StartTime,Dur,Proto,SrcAddr,Sport,Dir,
                   DstAddr,Dport,State,sTos,dTos,TotPkts,
                   TotBytes,SrcBytes,srcUdata,dstUdata,Label\n'
    Botnet 50:    'StartTime,Dur,Proto,SrcAddr,Sport,Dir,
                   DstAddr,Dport,State,sTos,dTos,TotPkts,
                   TotBytes,SrcBytes,Label\n'
    Botnet 367-1: 'StartTime,Dur,Proto,SrcAddr,Sport,Dir,
                   DstAddr,Dport,State,sTos,dTos,TotPkts,
                   TotBytes,SrcBytes,SrcPkts,Label\n'

    """

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
        _filter_protocols = (
            len(protocols) > 0
            or (len(protocols) == 1 and 'any' in protocols)
        )
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
        logger.info(f"[+] wrote file '{outfilename}'")


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
    __CTU_DATASET_INDEX_URL__ = ('https://mcfp.felk.cvut.cz/'
                                 'publicDatasets/datasets.json')
    __NETFLOW_DATA_DIR__ = 'detailed-bidirectional-flow-labels/'
    # Put the cache file in user's home directory by default
    # (or fall back to cwd, just to be robust).
    __CACHE_FILE__ = os.environ.get(
        'LIM_CTU_CACHE',
        os.path.join(
            os.getenv('HOME', os.getcwd()), '.lim-ctu-cache.json')
    )
    __CACHE_TIMEOUT__ = 60 * 60 * 24 * 7  # secs * mins * hours * days
    # These are fields associated with files that can be downloaded.
    __ATTRIBUTES__ = [
        'ZIP',
        'LABELED',
        'BINETFLOW',
        'PCAP',
    ]
    __DATA_COLUMNS__ = [
        'ZIP',
        'LABELED',
        'BINETFLOW',
        'PCAP',
        'WEBLOGNG'
    ]
    __INDEX_COLUMNS__ = [
        'Infection_Date',
        'Capture_Name',
        'Malware',
        'MD5',
        'SHA256',
        'Capture_URL',
    ]
    # These are all columns, in the order we want them to occur in output.
    __ALL_COLUMNS__ = __INDEX_COLUMNS__ + __DATA_COLUMNS__
    __MIN_COLUMNS__ = 3
    __DISCLAIMER__ = textwrap.dedent("""\
       When publishing content derived from this data, make sure to respect
       the Disclaimer at the bottom of the scenario ``Readme.*`` files:

       ::

          These files were generated in the Stratosphere Lab as part of the
          Malware Capture Facility Project in the CVUT University, Prague,
          Czech Republic.  The goal is to store long-lived real botnet traffic
          and to generate labeled netflows files.

          Any question feel free to contact us:
          Sebastian Garcia: sebastian.garcia@agents.fel.cvut.cz

          You are free to use these files as long as you reference this project
          and the authors as follows:

          Garcia, Sebastian. Malware Capture Facility Project. Retrieved
          from https://stratosphereips.org


       To cite the [CTU13] dataset please cite the paper "An empirical
       comparison of botnet detection methods" Sebastian Garcia, Martin Grill,
       Jan Stiborek and Alejandro Zunino. Computers and Security Journal,
       Elsevier. 2014. Vol 45, pp 100-123.
       http://dx.doi.org/10.1016/j.cose.2014.05.011

    """)  # noqa

    def __init__(self,
                 async_timeout=__ASYNC_TIMEOUT__,
                 semaphore_limit=__SEMAPHORE_LIMIT__,
                 cache_file=None,
                 ignore_cache=False,
                 debug=False):
        """Initialize object."""

        self.semaphore_limit = semaphore_limit
        self.async_timeout = async_timeout
        self.cache_file = \
            cache_file if cache_file is not None else self.__CACHE_FILE__
        self.ignore_cache = ignore_cache
        self.debug = debug
        self.full_names = None
        self.short_map = None
        self._metadata = {
            'columns': [],
            'scenarios': {},
            'index': [],
            'reverse_index': {},
        }
        pass

    @classmethod
    def get_ctu_dataset_index(
        cls,
        reference_file=None,
        reference_timestamp=0
    ):
        """Get the CTU Dataset index.

        If a reference file is provided, the last modified time of this
        file is used to avoid unecessarily downloading a file. Alternatively,
        specifying a reference timestamp allows the same ability without the
        requirement that a file exist. Use one or the other.

        Args:
            reference_file (str): Absolute file path to reference file
            reference_timestamp (int): Unix epoch timestamp

        Returns:
            dataset (dict): Dictionary with index
        """

        if reference_timestamp != 0:
            if reference_file is not None:
                raise RuntimeError(
                    "[!] don't use both 'reference_timestamp' "
                    "and 'reference_file'")
            else:
                reference_timestamp = get_file_last_mtime(
                    file_path=os.path.abspath(reference_file))
        url = cls.__CTU_DATASET_INDEX_URL__
        dataset_json = get_if_newer(url,
                                    reference_timestamp)
        dataset_index = json.loads(dataset_json)
        return dataset_index

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
    def get_column_string(cls, string=None):
        """Return caseless match for column string.

        Args:
            string (str): Candidate string
        Returns:
            (str): Proper matching column string
        """
        if string is None:
            raise RuntimeError('[-] string must not be None')
        match = [
            s for s in cls.__ALL_COLUMNS__
            if s.lower() == string.lower()
        ]
        try:
            return match.pop()
        except IndexError:
            pass
        raise RuntimeError(f"[-] '{string}' doesn't match any column string")

    @classmethod
    def get_data_columns(cls):
        """Returns list of data columns"""
        return [c for c in cls.__DATA_COLUMNS__]

    @classmethod
    def get_index_columns(cls, min=True):
        """Returns list of index columns"""
        columns = [c for c in cls.__INDEX_COLUMNS__]
        if min:
            return columns[:cls.__MIN_COLUMNS__]
        else:
            return columns

    @classmethod
    def get_all_columns(cls):
        """Returns list of all available columns"""
        return [c for c in cls.__ALL_COLUMNS__]

    @classmethod
    def get_disclaimer(cls):
        """Returns CTU disclaimer"""
        return cls.__DISCLAIMER__

    def get_fullname(self, name=None):
        """
        Return a full scenario name from a possibly abbreviated name.

        Break the string on dash characters and see if the components
        can be combined with "CTU-" and "Capture-" to create a valid
        Capture_Name.

        Examples:
            Full name: CTU-Malware-Capture-Botnet-116-1
            Short names: Malware-Botnet-116-1, Botnet-116-1, 116-1
        Args:
            name (str): Name string or substring

        Returns:
          (str) Full name of capture if only one is found

        Raises:
            RuntimeError with suggestions for fixing problem
        """
        if name is None:
            raise RuntimeError('[-] no name specified')
        if self.full_names is None:
            # Cache results for subsequent calls
            self.full_names = [
                n for n in self._metadata.get('reverse_index').keys()
            ]
        if self.short_map is None:
            # Cache results for subsequent calls
            self.short_map = {
                self.get_shortname(n): n
                for n in self.full_names
            }
        if name in self.full_names:
            return name
        if name in self.short_map:
            return self.short_map[name]
        # A short name looks like this: Malware-Botnet-116-1
        # Get numeric suffix first (full name must end with this).
        m = re.search(r'([0-9]+[-]{0,1}[0-9][0-9]*)$', name)
        if m is None:
            if name.find('-') == -1:
                sys.exit(f"[-] short scenario names required a '-': "
                         f"use '--name-includes \"{name}\"'' instead")
            return None
        number = m.group(0).lstrip('-')
        # Split the rest of the name on dashes.
        # Result looks like this: ['Malware', 'Botnet']
        parts = name.rstrip(number).split('-')
        # Symbolic value for .find() not finding something
        MISSING = -1
        for n in self.full_names:
            if not n.endswith(f"-{number}"):
                continue
            found_part = [
                n.find(f"{part}-")
                for part in parts
            ]
            if MISSING not in found_part:
                return n
        return None

    def get_shortname(self, name):
        """
        Return a short scenario name from a full scenario.

        Strips off the substrings 'CTU-' and 'Capture-', returning
        the remainder of the 'Capture_Name' field.

        Before: CTU-Malware-Capture-Botnet-91
        After: Malware-Botnet-91

        Args:
            name (str): Capture name

        Returns:
            (str) Name without above substrings
        """

        return name.replace('CTU-', '').replace('Capture-', '')

    @classmethod
    def filename_from_url(cls, url=None):
        if url is None:
            return None
        filename = url.split('/').pop()
        if filename in ['', None]:
            raise RuntimeError(
                f"[-] cannot determine filename from url {url}")
        return filename

    def get_scenarios(self):
        """Returns CTU dataset scenarios"""
        return self._metadata['scenarios']

    def get_scenario_names(self):
        """Returns CTU dataset scenario names"""
        return [s for s in self._metadata['scenarios'].keys()]

    def is_valid_scenario(self, name):
        """Returns boolean indicating existence of scenario"""
        if name is None:
            return False
        if type(name) is not str:
            raise RuntimeError(f"[-] '{name}' must be type(str)")
        return name in self._metadata['scenarios']

    def get_scenario(self, name):
        """Returns CTU dataset scenario"""
        return self._metadata['scenarios'].get(name)

    def get_scenario_index(self, name):
        """Returns CTU dataset index for scenario"""
        i = self._metadata['reverse_index'].get(name)
        if i is None:
            return i
        return self._metadata['index'][i]

    def get_extended_columns(self):
        """Returns extended CTU dataset columns"""
        return self.__ALL_COLUMNS__

    def get_extended_data(self, name):
        """Returns extended CTU dataset data.

        This is a combination of the columns from the CTU JSON
        index, plus the data elements that were extracted from the
        capture description pages.
        """
        i = self._metadata['reverse_index'].get(name)
        if i is None:
            return i
        items = self._metadata['index'][i]
        data = [
            items.get(k)
            for k in self.__INDEX_COLUMNS__
        ]
        for c in self.__DATA_COLUMNS__:
            data.append(self._metadata['scenarios'][name].get(c))
        return data

    def get_scenario_page(self, name):
        """Returns CTU dataset scenario HTML page"""
        full_name = self.get_fullname(name)
        try:
            return self._metadata.get('scenarios').get(full_name).get('_PAGE')
        except Exception as err:  # noqa
            return None

    def get_scenario_data(self, name, attribute):
        """
        Returns CTU scenario dataset attribute.

        Discrete attributes are returned as they are.

        Compound attributes (i.e., files) are composed of the
        base URL plus the attribute's name (which may include path
        information).
        """
        scenarios = self._metadata['scenarios']
        if name not in scenarios:
            return None
        scenario_data = scenarios.get(name)
        scenario_index = self.get_scenario_index(name)
        scenario_url = scenario_index.get('Capture_URL')
        if attribute == 'Capture_URL':
            return scenario_url
        attribute = attribute.upper()
        attributes = self.get_data_columns()
        if attribute in attributes:
            try:
                result = f"{scenario_url}/{scenario_data.get(attribute)}"
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
        name = self.get_fullname(name=name)
        url = self.get_scenario_data(name, attribute)
        if url in ['', None]:
            logger.info(f"[-] scenario '{name}' does not have "
                        f"'{attribute}' data: skipping")
        else:
            # 'https://mcfp.felk.cvut.cz/publicDatasets/CTU-Mixed-Capture-1/2015-07-28_mixed.pcap'
            if filename is None:
                filename = self.filename_from_url(url)
                # '2015-07-28_mixed.pcap'
            full_path = os.path.join(data_dir, filename)
            self.fetch_scenario_content_byurl(url, filename=full_path)

    # https://pawelmhm.github.io/asyncio/python/aiohttp/2016/04/22/asyncio-aiohttp.html

    def load_ctu_metadata(self):
        """Ensure all required metadata is loaded in object.

        This includes the attributes described by the JSON index file,
        plus the descriptions of each capture scenario and data files
        that were identified from each capture's web page.  These are
        updated at the same time and a local cache is kept to minimize
        load on the CTU servers.
        """

        if not self.cache_needs_refresh(force_refresh=self.ignore_cache):
            self.read_cache()
        else:
            logger.info(f"[+] generating metadata cache '{self.cache_file}'")
            # Populate index
            self._metadata['index'] = self.get_ctu_dataset_index()
            # Populate scenarios
            loop = asyncio.get_event_loop()
            loop.add_signal_handler(signal.SIGINT, loop.stop)
            future = asyncio.ensure_future(self.run_fetch())
            loop.run_until_complete(future)
            # Somewhat painful attempt to validate index keys match
            # what is defined in this class.
            used = set()
            columns = [
                k
                for i in self._metadata.get('index')
                for k in i.keys()
                if k not in used and (used.add(k) or True)
            ]
            extra_keys = [
                c for c in columns
                if c not in self.__INDEX_COLUMNS__
            ]
            if len(extra_keys) > 0:
                raise RuntimeError(
                    "[!] incorrect or new index key"
                    f"{'' if len(extra_keys) == 1 else 's'}: "
                    f"{','.join(extra_keys)}"
                )
            self._metadata['columns'] = [c for c in columns]
            # Populate reverse index
            for i, item in enumerate(self._metadata['index']):
                self._metadata['reverse_index'][item.get('Capture_Name')] = i
            # Dump to cache
            self.write_cache()

    async def record_scenario_metadata(self, semaphore, name, url, session):
        if url is None:
            raise RuntimeError('[-] url must not be None')
        if url.find('publicDatasets') == -1:
            raise RuntimeError('[-] url does not contain "publicDatasets"')
        if name in self._metadata['scenarios']:
            raise RuntimeError(f"[-] scenario '{name}' already exists")
        self._metadata['scenarios'][name] = dict()
        _scenario = self._metadata['scenarios'][name]
        page = await self.fetch_page(semaphore, url, session)
        # Save name parts for later abbreviated name matching
        # TODO(dittrich): This isn't used yet...
        _scenario['_NAME_PARTS'] = name.split('-')
        # Underscore on _page means ignore later (logic coupling)
        _scenario['_PAGE'] = page
        _scenario['_SUCCESS'] = (
            page not in ["", None] and "Not Found" not in page
        )
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
                if href_ext in self.__DATA_COLUMNS__:
                    _scenario[href_ext] = href
        pass

    async def run_fetch(self):
        tasks = []
        semaphore = asyncio.Semaphore(self.semaphore_limit)
        session = None
        try:
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(verify_ssl=False)) as session:  # noqa
                for scenario in self._metadata.get('index'):
                    url = scenario.get('Capture_URL')
                    name = scenario.get('Capture_Name')
                    # TODO(dittrich): Remove when done refactoring
                    # self._metadata['scenarios'][name] = dict()
                    task = asyncio.ensure_future(
                        self.record_scenario_metadata(
                            semaphore, name, url, session))
                    tasks.append(task)
                responses = asyncio.gather(*tasks)
                logger.info(f'[+] queued {len(tasks)} pages for processing')
                await responses
        except KeyboardInterrupt:
            if session is not None:
                session.close()

    async def fetch_page(self, semaphore, url, session):
        """Fetch a page"""
        if self.debug:
            logger.debug(f'[+] fetch_page({url})')
        page = await self.bound_fetch(semaphore, url, session)
        return page.decode("utf-8")

    async def bound_fetch(self, semaphore, url, session):
        """Fetch a page asynchronously with semaphore limiting"""
        async with semaphore:
            return await self.fetch(url, session)

    async def fetch(self, url, session):
        """GET a URL asynchronously"""
        with async_timeout.timeout(self.async_timeout):
            logger.debug(f'[+] fetch({url})')
            async with session.get(url) as response:
                return await response.read()

    def immediate_fetch(self, url):
        """GET a page synchronously"""
        if self.debug:
            logger.debug(f'[+] immediate_fetch({url})')
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            requests.packages.urllib3.disable_warnings(
                category=InsecureRequestWarning)
            response = requests.get(url, verify=False)  # nosec
        return response

    def cache_needs_refresh(
        self,
        source_mtime=0,
        force_refresh=False,
    ):
        """
        Determine if the local cache needs to be refreshed.

        The local cache file is considered to be "expired" if the
        last modification time of the source JSON index file from
        the CTU web site is newer than that of the local cache.
        This assumes that the description pages for each capture
        in the index have themselves not be updated independantly
        of the index.

        A timeout period is used to reduce the number of checks for
        the source index file. If the cache file has been modified
        within the timeout period, it is assumed to still be valid.

        For the purposes of testing, a cache file that starts with
        'test-' will appear to never be expired.

        Arguments:
            source_mtime (int): Unix epoch timestamp for source's
                                last modified time. Default: 0
            force_check (bool): Ignore the timeout and check timestamps

        Returns:
            True if cache_file needs to be refreshed or False if
            it does not.
        """

        # Assume cache has expired unless proven otherwise.
        CACHE_EXPIRED = True
        if self.cache_file.startswith('test'):
            return not CACHE_EXPIRED
        cache_last_mtime = get_file_last_mtime(file_path=self.cache_file,
                                               clean=True)
        if cache_last_mtime == 0:
            logger.debug(
                f"[+] cache '{self.cache_file}' does not exist")
            return CACHE_EXPIRED
        # BUG - FIX THIS
        # if source_mtime == 0 or force_refresh:
        #     logger.debug(
        #         f"[+] forcing refresh of cache '{self.cache_file}'")
        #     return CACHE_EXPIRED
        if source_mtime > cache_last_mtime:
            logger.debug(
                f"[+] cache '{self.cache_file}' is out of date "
                "with respect to 'source_mtime'")
            return CACHE_EXPIRED
        # Limit checks against source URL's 'Last_Modified' header.
        now = int(time.time())
        accept_limit = now - self.__CACHE_TIMEOUT__
        if cache_last_mtime > accept_limit:
            logger.debug(
                f"[+] cache '{self.cache_file}' age "
                "is within acceptable timeout")
            return not CACHE_EXPIRED
        logger.debug(
            f"[+] cache '{self.cache_file}' has expired")
        return CACHE_EXPIRED

    def read_cache(self, force_refresh=False):
        """
        Load index metadata from a local cache.

        In order to minimize load on the CTU dataset server, the
        metadata index and related information is cached locally
        and only refreshed if it is considered expired. If there is
        no cache, or if the last modification time of the remote index
        is greater (newer) than the last modified time local cache, the
        cache is refreshed.

        Returns:
            None
        """

        url = self.__CTU_DATASET_INDEX_URL__
        if self.cache_needs_refresh(force_refresh=force_refresh):
            cache_last_mtime = get_file_last_mtime(file_path=self.cache_file)
            index_last_mtime = get_url_last_modified(url=url)
            if force_refresh or self.cache_needs_refresh(
                source_mtime=index_last_mtime
            ):
                datasets_json = get_if_newer(url,
                                             cache_last_mtime)
                self._metadata = json.loads(datasets_json)
            self.write_cache()
        else:
            with open(self.cache_file, 'r') as infile:
                self._metadata = json.load(infile)
        if self.full_names is None:
            # Cache results for subsequent calls
            self.full_names = [
                n for n in self._metadata.get('reverse_index').keys()
            ]
        if self.short_map is None:
            # Cache results for subsequent calls
            self.short_map = {
                self.get_shortname(n): n
                for n in self.full_names
            }

        logger.debug(
            f"[+] loaded metadata from cache: '{self.cache_file}'")

    def write_cache(self):
        """Save metadata to local cache as JSON"""

        with open(self.cache_file, 'w') as outfile:
            json.dump(self._metadata, outfile)
        logger.debug(
            f"[+] wrote new cache file '{self.cache_file}'")
        return True

    def delete_cache(self):
        """Delete cache file"""

        os.remove(self.cache_file)
        logger.debug(f"[+] deleted cache file '{self.cache_file}'")
        return True

    def get_metadata(self,
                     columns=None,
                     malware_includes=None,
                     name_includes=None,
                     fullnames=False,
                     description_includes=None,
                     date_starting=None,
                     date_ending=None,
                     has_hash=None):
        """
        Return a list of lists of data suitable for use by
        cliff, following the order of elements in 'columns'.
        """
        if columns is None:
            columns = self.__INDEX_COLUMNS__
        else:
            columns = [
                self.get_column_string(c)
                for c in columns
            ]
        data = []
        # TODO(dittrich): Make this more DRY.
        for dataset in self._metadata.get('index'):
            name = dataset.get('Capture_Name')

            metadata = self._metadata['scenarios'][name]
            match = True
            if name_includes is not None:
                scenario = str(dataset.get('Capture_Name')).lower()
                find = scenario.find(name_includes.lower())
                match = match and (find != -1)
            if malware_includes is not None:
                # Can't look for something that doesn't exist.
                if 'Malware' not in dataset:
                    continue
                malware_name = str(dataset.get('Malware')).lower()
                find = malware_name.find(malware_includes.lower())
                match = match and (find != -1)
            if description_includes is not None:
                # Can't look for something that doesn't exist.
                page = metadata.get('_PAGE').lower()
                find = page.find(description_includes.lower())
                match = match and (find != -1)
            if has_hash is not None:
                match = match and (
                    has_hash == dataset.get('MD5', '')
                    or has_hash == dataset.get('SHA256', '')
                )
            match = match and (
                date_ge(dataset.get('Infection_Date'), date_starting)
                and date_le(dataset.get('Infection_Date'), date_ending)
            )
            if match:
                # Now create row list by combining dataset and
                # metadata dict elements.
                row = {**dataset, **metadata}
                data.append([row.get(c) for c in columns])
        return data


all = [
    unhex,
    IPv4ToID,
    download_ctu_netflow,
    CTU_Dataset,
]


# vim: set ts=4 sw=4 tw=0 et :
