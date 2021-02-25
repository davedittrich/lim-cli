# -*- coding: utf-8 -*-

import os
import pathlib
import pbr.version


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
    __version__ = '21.2.4'
    __release__ = __version__


__author__ = 'Dave Dittrich'
__email__ = 'dave.dittrich@gmail.com'


# vim: set ts=4 sw=4 tw=0 et :
