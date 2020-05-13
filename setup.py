#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Setup script for the LiminalAI CLI utility
#
# Author: Dave Dittrich <dave.dittrich@gmail.com>
# URL: ...

import codecs
import os
import re

from setuptools import find_packages, setup


PROJECT = 'lim'

try:
    with open('README.rst') as readme_file:
        long_description = readme_file.read()
except IOError:
    long_description = ''

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
    name='lim',
    pbr=True,
    # version=get_version('lim', '__init__.py'),
    #
    description="Python CLI for LiminalAI",
    long_description=long_description + "\n\n" + history,

    author="Dave Dittrich",
    author_email='dave.dittrich@gmail.com',

    url='https://github.com/LiminalAI/lim',
    download_url='https://github.com/LiminalAI/lim/tarball/master',

    namespace_packages=[],
    packages=find_packages(),
    package_dir={'lim':
                 'lim'},
    include_package_data=True,

    python_requires='>=3.6,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*',
    install_requires=get_contents('requirements.txt'),

    license="Apache Software License",
    keywords='lim',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Other Audience',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],

    test_suite='tests',

    entry_points={
        'console_scripts': [
            'lim = lim.main:main',
        ],
        'lim': [
            'about = lim.about:About',
            'ctu get = lim.ctu:CTUGet',
            'ctu list = lim.ctu:CTUList',
            'ctu stats = lim.ctu:CTUStats',
            'ctu overview = lim.ctu:CTUOverview',
            'cafe admin endpoints = lim.packet_cafe.admin.endpoints:Endpoints',
            'cafe admin files = lim.packet_cafe.admin.files:Files',
            'cafe admin results = lim.packet_cafe.admin.results:Results',
            'cafe admin sessions = lim.packet_cafe.admin.sessions:Sessions',
            'cafe admin info = lim.packet_cafe.admin.info:AdminInfo',
            'cafe endpoints = lim.packet_cafe.api.endpoints:Endpoints',
            'cafe info = lim.packet_cafe.api.info:ApiInfo',
            'cafe raw = lim.packet_cafe.api.raw:Raw',
            'cafe requests = lim.packet_cafe.api.requests:Requests',
            'cafe status = lim.packet_cafe.api.status:Status',
            'cafe tools = lim.packet_cafe.api.tools:Tools',
            'cafe upload = lim.packet_cafe.api.upload:Upload',
            'pcap extract ips = lim.pcap:PCAPExtract',
            'pcap shift network = lim.pcap:PCAPShift',
            'pcap shift time = lim.pcap:PCAPShift',
        ],
    },
    zip_safe=False,
)
