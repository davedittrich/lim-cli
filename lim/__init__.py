# -*- coding: utf-8 -*-

import datetime
import os
import pbr.version

version_info = pbr.version.VersionInfo('lim')
try:
    __version__ = version_info.version_string()
except AttributeError:
    __version__ = '20.5.0'

try:
    __release__ = version_info.release_string()
except AttributeError:
    __release__ = '20.5.0'

this_year = datetime.datetime.today().year
COPYRIGHT = f"""
Author:    Dave Dittrich <dave.dittrich@gmail.com>
Copyright: 2018-{ this_year }, Dave Dittrich. 2019-{ this_year }, Liminal Information Corp.
License:   Apache 2.0 License
URL:       https://pypi.python.org/pypi/lim-cli
"""  # noqa

BUFFER_SIZE = 128 * 1024
DAY = os.environ.get('DAY', 5)
DEFAULT_PROTOCOLS = ['icmp', 'tcp', 'udp']
KEEPALIVE = 5.0
LIM_DATA_DIR = os.environ.get('LIM_DATA_DIR', os.getcwd())
MAX_LINES = None
MAX_ITEMS = 10
# Use syslog for logging?
# TODO(dittrich): Make this configurable, since it can fail on Mac OS X
SYSLOG = False

__author__ = 'Dave Dittrich'
__email__ = 'dave.dittrich@gmail.com'


def copyright():
    """Copyright string"""
    return COPYRIGHT


# vim: set ts=4 sw=4 tw=0 et :
