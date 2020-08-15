#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Setup script for the LiminalInfo CLI utility
#
# Author: Dave Dittrich <dave.dittrich@gmail.com>
# Copyright: 2018-2020, Dave Dittrich. 2019-2020, Liminal Information Corp.
# URL: https://github.com/davedittrich/lim

import codecs
import os
import re

from setuptools import setup, find_packages

# Package meta-data.
NAME = 'lim-cli'
DESCRIPTION = 'LiminalInfo command line app.'
URL = 'https://github.com/davedittrich/lim-cli'
DOWNLOAD_URL = 'https://github.com/davedittrich/lim-cli/tarball/master'
EMAIL = 'dave.dittrich@gmail.com'
AUTHOR = 'Dave Dittrich'
PYTHON_REQUIRES = '>=3.6.0'

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


def get_version(*args):
    """Extract the version number from a Python module."""
    contents = get_contents(*args)
    metadata = dict(re.findall('__([a-z]+)__ = [\'"]([^\'"]+)', contents))
    return metadata['version']


def get_absolute_path(*args):
    """Transform relative pathnames into absolute pathnames."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), *args)


setup(
    name=NAME,
    pbr=True,
    description=DESCRIPTION,
    long_description=long_description + "\n\n" + history,
    long_description_content_type=long_description_content_type,

    author=AUTHOR,
    author_email=EMAIL,

    url=URL,
    download_url=DOWNLOAD_URL,

    namespace_packages=[],
    packages=find_packages(exclude=['tests']),
    package_dir={'lim':
                 'lim'},
    include_package_data=True,
    # Make sure this matches tox.ini!
    setup_requires=['pbr>=5.4.5', 'setuptools>=40.9.0'],
    python_requires=PYTHON_REQUIRES,
    install_requires=get_contents('requirements.txt'),

    license="Apache Software License",
    keywords='lim',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Other Audience',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Security',
        'Topic :: Utilities',
    ],

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
            'cafe containers = lim.packet_cafe.extensions.containers:Containers',  # noqa
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
