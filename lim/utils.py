# -*- coding: utf-8 -*-

import logging
import os
import subprocess  # nosec
import sys
import requests
import time

from bz2 import BZ2Decompressor
from collections import OrderedDict


log = logging.getLogger(__name__)


def find(lst, key, value):
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return i
    return None


def convert_type(t, v):
    """Convert value 'v' to type 't'"""
    _valid_type = ['int', 'float', 'long', 'complex', 'str']
    if t not in _valid_type:
        raise RuntimeError('[-] unsupported type: must be one of: ' +
                           ",".join([i for i in _valid_type]))
    try:
        return type(eval("{}()".format(t)))(v)   # nosec
    except ValueError:
        raise ValueError('type={}, value="{}"'.format(t, v))


def check_natural(value):
    try:
        i = int(value)
    except ValueError:
        raise RuntimeError('[-] "{}" is not a base-10 integer'.format(value))
    if not i > 0:
        raise RuntimeError('[-] {} is not a natural number (>0)'.format(value))
    return i


def check_whole(value):
    try:
        i = int(value)
    except ValueError:
        raise RuntimeError('[-] "{}" is not a base-10 integer'.format(value))
    if not i >= 0:
        raise RuntimeError('[-] {} is not a whole number (>=0)'.format(value))
    return i


def elapsed(start, end):
    assert isinstance(start, float)
    assert isinstance(end, float)
    assert start >= 0.0
    assert start <= end
    hours, rem = divmod(end - start, 3600)
    minutes, seconds = divmod(rem, 60)
    return "{:0>2}:{:0>2}:{:05.2f}".format(
        int(hours), int(minutes), seconds)


def get_output(cmd=['echo', 'NO COMMAND SPECIFIED'],
               cwd=os.getcwd(),
               stderr=subprocess.STDOUT,
               shell=False):
    """Use subprocess.check_ouput to run subcommand"""
    output = subprocess.check_output(  # nosec
            cmd,
            cwd=cwd,
            stderr=stderr,
            shell=shell
        ).decode('UTF-8').splitlines()
    return output


class Timer(object):
    """
    Timer object usable as a context manager, or for manual timing.
    Based on code from http://coreygoldberg.blogspot.com/2012/06/python-timer-class-context-manager-for.html  # noqa

    As a context manager, do:

        from timer import Timer

        url = 'https://github.com/timeline.json'

        with Timer() as t:
            r = requests.get(url)

        print 'fetched %r in %.2f millisecs' % (url, t.elapsed*1000)

    """

    def __init__(self, task_description='elapsed time', verbose=False):
        self.verbose = verbose
        self.task_description = task_description
        self.laps = OrderedDict()

    def __enter__(self):
        """Record initial time."""
        self.start(lap="__enter__")
        if self.verbose:
            sys.stdout.write('{}...'.format(self.task_description))
            sys.stdout.flush()
        return self

    def __exit__(self, *args):
        """Record final time."""
        self.stop()
        backspace = '\b\b\b'
        if self.verbose:
            sys.stdout.flush()
            if self.elapsed_raw() < 1.0:
                sys.stdout.write(backspace + ':' + '{:.2f}ms\n'.format(
                    self.elapsed_raw() * 1000))
            else:
                sys.stdout.write(backspace + ': ' + '{}\n'.format(
                    self.elapsed()))
            sys.stdout.flush()

    def start(self, lap=None):
        """Record starting time."""
        t = time.time()
        first = None if len(self.laps) == 0 \
            else self.laps.iteritems().next()[0]
        if first is None:
            self.laps["__enter__"] = t
        if lap is not None:
            self.laps[lap] = t
        return t

    def lap(self, lap="__lap__"):
        """
        Records a lap time.
        If no lap label is specified, a single 'last lap' counter will be
        (re)used. To keep track of more laps, provide labels yourself.
        """
        t = time.time()
        self.laps[lap] = t
        return t

    def stop(self):
        """Record stop time."""
        return self.lap(lap="__exit__")

    def get_lap(self, lap="__exit__"):
        """Get the timer for label specified by 'lap'"""
        return self.lap[lap]

    def elapsed_raw(self, start="__enter__", end="__exit__"):
        """Return the elapsed time as a raw value."""
        return self.laps[end] - self.laps[start]

    def elapsed(self, start="__enter__", end="__exit__"):
        """
        Return a formatted string with elapsed time between 'start'
        and 'end' kwargs (if specified) in HH:MM:SS.SS format.
        """
        hours, rem = divmod(self.elapsed_raw(start, end), 3600)
        minutes, seconds = divmod(rem, 60)
        return "{:0>2}:{:0>2}:{:05.2f}".format(
            int(hours), int(minutes), seconds)


def safe_to_open(filename, overwrite=False):
    """Ensure that file can be opened without over-writing (unless --force)"""
    if os.path.exists(filename):
        statinfo = os.stat(filename)
        if statinfo.st_size > 0 and not overwrite:
            raise RuntimeError('[-] file "{}" exists; '.format(filename) +
                               'use --force to overwrite.')
    return True


class BZ2_LineReader(object):
    """
    Class to implement an iterator outputting individual JSON records from
    BZ2 compressed data hosted at a specific URL. Based on code example from:
    https://stackoverflow.com/questions/47778579/how-to-read-lines-from-arbitrary-bz2-streams-for-csv
    """
    def __init__(self, url=None, buffer_size=6*1024, verify=True):
        self.url = url
        self.buffer_size = buffer_size
        self.verify = verify
        self.bytes_transferred = 0
        self.decompressor = BZ2Decompressor()
        self.buffer = ''
        self.first_line = None

    def __len__(self):
        return self.bytes_transferred

    def first_line(self):
        """Return the first line read (header?)"""
        return self.first_line

    def readlines(self, maxlines=None):
        with requests.get(self.url,
                          stream=True,
                          verify=self.verify) as file:
            if file.status_code in [404]:
                raise RuntimeError('[-] file not found: {}'.format(self.url))
            for row in self._line_reader(file, maxlines=maxlines):
                yield row

    def _line_reader(self, file, maxlines=None):
        count = 0
        for chunk in file.iter_content(chunk_size=self.buffer_size):
            self.bytes_transferred += len(chunk)
            block = self.decompressor.decompress(chunk)
            if sys.version_info >= (3,):  # Python 3
                block = block.decode('utf-8')  # Convert bytes to string.
            if block:
                self.buffer += block
            if '\n' in self.buffer or '\r\n' in self.buffer:
                lines = self.buffer.splitlines(True)
                if lines:
                    self.buffer = ''\
                        if lines[-1].endswith('\n')\
                        or lines[-1].endswith('\r\n')\
                        else lines.pop()
                    for line in lines:
                        if self.first_line is None:
                            self.first_line = line
                        yield line
                        count += 1
                        if maxlines is not None and count == int(maxlines):
                            raise StopIteration


class LineReader(object):
    """
    Class to implement an iterator outputting individual lines from
    uncompressed data hosted at a specific URL. Based on code example from:
    https://stackoverflow.com/questions/47778579/how-to-read-lines-from-arbitrary-bz2-streams-for-csv
    """
    def __init__(self, url=None, buffer_size=6*1024, verify=True):
        self.url = url
        self.buffer_size = buffer_size
        self.verify = verify
        self.bytes_transferred = 0
        self.buffer = ''
        self.first_line = None

    def __len__(self):
        return self.bytes_transferred

    def first_line(self):
        """Return the first line read (header?)"""
        return self.first_line

    def readlines(self, maxlines=None):
        with requests.get(self.url,
                          stream=True,
                          verify=self.verify) as file:
            if file.status_code in [404]:
                raise RuntimeError('[-] file not found: {}'.format(self.url))
            for row in self._line_reader(file, maxlines=maxlines):
                yield row

    def _line_reader(self, file, maxlines=None):
        count = 0
        for block in file.iter_content(chunk_size=self.buffer_size):
            self.bytes_transferred += len(block)
            if sys.version_info >= (3,):  # Python 3
                block = block.decode('utf-8')  # Convert bytes to string.
            if block:
                self.buffer += block
            if '\n' in self.buffer or '\r\n' in self.buffer:
                lines = self.buffer.splitlines(True)
                if lines:
                    self.buffer = ''\
                        if lines[-1].endswith('\n')\
                        or lines[-1].endswith('\r\n')\
                        else lines.pop()
                    for line in lines:
                        if self.first_line is None:
                            self.first_line = line
                        yield line
                        count += 1
                        if maxlines is not None and count >= int(maxlines):
                            raise StopIteration

# vim: set ts=4 sw=4 tw=0 et :
