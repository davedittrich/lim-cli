===
lim
===

.. image:: https://img.shields.io/pypi/v/lim-cli.svg
       :target: https://pypi.python.org/pypi/lim-cli
       :alt: PyPi Status

.. image:: https://github.com/davedittrich/lim-cli/workflows/CICD/badge.svg
       :target: https://github.com/davedittrich/lim-cli/actions
       :alt: GitHub Actions Status

.. image:: https://img.shields.io/travis/davedittrich/lim-cli.svg
       :target: https://travis-ci.org/davedittrich/lim-cli
       :alt: Travis.ci Status

.. image:: https://readthedocs.org/projects/lim-cli/badge/?version=latest
       :target: https://lim-cli.readthedocs.io/en/latest/?badge=latest
       :alt: Documentation Status


The ``lim`` app is a command line interface that provides a common
means of interactively accessing multiple network security tools
and data sources, or allowing you to do so from your own scripts
or from existing security event processing and automation platforms.

``lim`` uses the `openstack/cliff`_ framework to organize features into related
groups of subcommands with lots of built-in help internally documenting their use.
It produces output in clean tabular form, or in several other data formats that
can feed into yet other network security tools or automation platforms.

Using ``lim``, you can learn skills a SOC analyst needs to understand how
malicious software communicates on the network, or script the post-processing
of network traffic traffic captures from a honeypot or your own network.


* License: Apache 2.0 License
* Documentation: https://lim-cli.readthedocs.io/en/latest/


Features
--------

* Uses the `openstack/cliff`_ command line framework.
* Serves as a CLI for the `CTU Malware Capture Facility Datasets`_.
* Serves as a CLI for In-Q-Tel Labs' `Packet Café`_ service.
* Provides basic reporting on `Packet Café`_ worker output.
* Provides basic `PCAP`_ file manipulation capabilities.
* Future features include plotting and graphing of output
  from PCAP processing.

.. _openstack/cliff: https://github.com/openstack/cliff
.. _CTU Malware Capture Facility Datasets: https://www.stratosphereips.org/datasets-overview
.. _Packet Café: https://www.cyberreboot.org/projects/packet-cafe/
.. _PCAP: https://www.tcpdump.org/pcap.html

.. EOF
