#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Setup script for the LiminalInfo CLI utility
#
# Author: Dave Dittrich <dave.dittrich@gmail.com>
# Copyright: 2018-2020, Dave Dittrich. 2019-2020, Liminal Information Corp.
# URL: https://github.com/davedittrich/lim

import codecs
import os
# import pkg_resources

from setuptools import setup, find_packages
from setuptools_scm import get_version

VERSION = str(get_version(root='.', relative_to=__file__)).split('+')[0]

try:
    with open('README.rst') as readme_file:
        long_description = readme_file.read()
        long_description_content_type = "text/x-rst"
except IOError:
    long_description = ''
    long_description_content_type = "text/plain"

try:
    with open('HISTORY.rst') as history_file:
        history = history_file.read().replace('.. :changelog:', '')
except IOError:
    history = ''


def get_contents(*args):
    """Get the contents of a file relative to the source distribution directory."""  # noqa
    with codecs.open(get_absolute_path(*args), 'r', 'UTF-8') as handle:
        return handle.read()


def get_absolute_path(*args):
    """Transform relative pathnames into absolute pathnames."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), *args)


setup(
    # Make sure this matches tox.ini!
    setup_requires=['setuptools>=40.9.0', 'pip>=20.2.2'],
    use_scm_version=True,
    long_description=long_description + "\n\n" + history,
    long_description_content_type=long_description_content_type,
    namespace_packages=[],
    package_dir={'lim': 'lim'},
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    install_requires=get_contents('requirements.txt'),
    test_suite='tests',
    entry_points={
        'console_scripts': [
            'lim = lim.__main__:main',
        ],
        'lim': [
            'about = lim.about:About',
            'ctu get = lim.ctu.get:CTUGet',
            'ctu list = lim.ctu.list:CTUList',
            'ctu show = lim.ctu.show:CTUShow',
            'ctu stats = lim.ctu.stats:CTUStats',
            'ctu overview = lim.ctu.overview:CTUOverview',
            'cafe about = lim.packet_cafe.about:About',
            'cafe admin delete = lim.packet_cafe.admin.delete:AdminDelete',
            'cafe admin endpoints = lim.packet_cafe.admin.endpoints:Endpoints',
            'cafe admin files = lim.packet_cafe.admin.files:Files',
            'cafe admin results = lim.packet_cafe.admin.results:Results',
            'cafe admin sessions = lim.packet_cafe.admin.sessions:Sessions',
            'cafe admin info = lim.packet_cafe.admin.info:AdminInfo',
            'cafe docker build = lim.packet_cafe.extensions.docker_cmds:ImagesBuild',  # noqa
            'cafe docker down = lim.packet_cafe.extensions.docker_cmds:ContainersDown',  # noqa
            'cafe docker images = lim.packet_cafe.extensions.docker_cmds:ImagesList',  # noqa
            'cafe docker pull = lim.packet_cafe.extensions.docker_cmds:ImagesPull',  # noqa
            'cafe docker ps = lim.packet_cafe.extensions.docker_cmds:ContainersList',  # noqa
            'cafe docker up = lim.packet_cafe.extensions.docker_cmds:ContainersUp',  # noqa
            'cafe endpoints = lim.packet_cafe.api.endpoints:Endpoints',
            'cafe raw = lim.packet_cafe.api.raw:Raw',
            'cafe requests = lim.packet_cafe.api.requests:Requests',
            'cafe results = lim.packet_cafe.api.results:Results',
            'cafe report = lim.packet_cafe.extensions.report:Report',
            'cafe info = lim.packet_cafe.api.info:ApiInfo',
            'cafe status = lim.packet_cafe.api.status:Status',
            'cafe stop = lim.packet_cafe.api.stop:Stop',
            'cafe tools = lim.packet_cafe.api.tools:Tools',
            'cafe upload = lim.packet_cafe.api.upload:Upload',
            'cafe ui = lim.packet_cafe.ui:UI',
            'pcap extract ips = lim.pcap.extract:PCAPExtract',
            'pcap shift network = lim.pcap.shift:PCAPShift',
            'pcap shift time = lim.pcap.shift:PCAPShift',
            'version = lim.about:About',
        ],
    },
    zip_safe=False,
)
