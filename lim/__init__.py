# -*- coding: utf-8 -*-

import os
import pathlib

__version__, __release__ = None, None

if __version__ is None:
    try:
        from setuptools_scm import get_version
        __version__ = get_version(root='..', relative_to=__file__)
        __release__ = __version__.split('+')[0]
    except (LookupError, ModuleNotFoundError):
        pass

if __version__ is None:
    from pkg_resources import get_distribution, DistributionNotFound
    try:
        __version__ = get_distribution("lim-cli").version
        __release__ = __version__
    except DistributionNotFound:
        pass

if __version__ is None:
    # PBR has a bug that produces incorrect version numbers
    # if you run ``psec --version`` in another Git repo.
    # This attempted workaround only uses PBR for getting
    # version and revision number if run in a directory
    # path that contains strings that appear to be
    # a python_secrets repo clone.
    import pbr.version
    p = pathlib.Path(os.getcwd())
    if 'lim-cli' in p.parts or 'lim' in p.parts:
        try:
            version_info = pbr.version.VersionInfo('lim')
            __version__ = version_info.cached_version_string()
            __release__ = version_info.release_string()
        except Exception:
            pass

if __version__ is None:
    __version__ = '21.2.6'
    __release__ = __version__


__author__ = 'Dave Dittrich'
__email__ = 'dave.dittrich@gmail.com'


# vim: set ts=4 sw=4 tw=0 et :
