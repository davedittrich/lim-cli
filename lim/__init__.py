# -*- coding: utf-8 -*-

import datetime
import os
import pathlib
import pbr.version
import textwrap

# PBR has a bug that produces incorrect version numbers
# if you run ``psec --version`` in another Git repo.
# This attempted workaround only uses PBR for getting
# version and revision number if run in a directory
# path that contains strings that appear to be
# a python_secrets repo clone.

p = pathlib.Path(os.getcwd())
if 'lim-cli' in p.parts or 'lim' in p.parts:
    try:
        version_info = pbr.version.VersionInfo('lim')
        __version__ = version_info.cached_version_string()
        __release__ = version_info.release_string()
    except Exception:
        pass
else:
    __version__ = '20.8.4'
    __release__ = __version__

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
    this_year = datetime.datetime.today().year
    copyright = textwrap.dedent(
        f"""Author:    Dave Dittrich <dave.dittrich@gmail.com>
        Copyright: 2018-{ this_year }, Dave Dittrich. 2019-{ this_year }, Liminal Information Corp.
        License:   Apache 2.0 License
        URL:       https://pypi.python.org/pypi/lim-cli""")  # noqa
    return copyright

# vim: set ts=4 sw=4 tw=0 et :
