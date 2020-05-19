=====
Usage
=====

Subcommand groups in ``lim`` are divided by categories reflecting (a) APIs for
services or data stores (e.g., ``cafe`` for `packet-cafe`_ or ``ctu`` for the
`CTU Datasets`_), or (b) by file type for utilities that process files of that
data type (e.g., ``pcap`` for PCAP file processing).

There is generally an ``about`` subcommand that helps get you to documentation
about those subcommands, which in most cases leads you to the appropriate web
site with online documentation.

Getting help
------------

To get help information on global command arguments and options, use
the ``help`` command or ``--help`` option flag. The usage documentation
below will detail help output for each command.

.. Can't just get --help output using autoprogram-cliff. :(
..
.. .. autoprogram-cliff:: lim
..    :application: lim.main
..    :arguments: --help

.. literalinclude:: lim-help.txt
    :language: console

..

About
-----

.. autoprogram-cliff:: lim
   :command: about

CTU
---

.. autoprogram-cliff:: lim
   :command: ctu *


Packet Cafe
-----------

.. autoprogram-cliff:: lim
   :command: cafe *


PCAP
----

.. autoprogram-cliff:: lim
   :command: pcap *


.. _packet-cafe: https://www.cyberreboot.org/projects/packet-cafe/
.. _CTU Datasets: https://www.stratosphereips.org/datasets-overview

.. EOF
