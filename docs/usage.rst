.. _usage:

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
..    :application: lim
..    :arguments: --help

.. literalinclude:: lim-help.txt
    :language: console

..

Formatters
----------

The `cliff`_ Command Line Formulation Framework provides a set of
formatting options that facilitate accessing and using stored secrets
in other applications. Data can be passed directly in a structured
format like CSV, or passed directly to programs like Ansible using
JSON.

.. attention::

    The formatter options are shown in the ``--help`` output for individual
    commands (e.g., ``lim cafe info --help``).  For the purposes of this
    chapter, including the lengthy formatter options on every command would be
    quite repetitive and take up a lot of space.  For this reason, the
    formatter options will be suppressed for commands as documented below.  The
    difference (**WITH** and **WITHOUT** the formatting options) would
    look like this:

    **WITH** formatting options

        .. autoprogram-cliff:: lim
           :command: cafe info

    **WITHOUT** formatting options

        .. autoprogram-cliff:: lim
           :command: cafe info
           :ignored: -f,-c,--quote,--noindent,--max-width,--fit-width,--print-empty,--sort-column

..

About
-----

.. autoprogram-cliff:: lim
   :command: about
   :ignored: -f,-c,--quote,--noindent,--max-width,--fit-width,--print-empty,--sort-column

Packet Cafe
-----------

.. autoprogram-cliff:: lim
   :command: cafe *
   :ignored: -f,-c,--quote,--noindent,--max-width,--fit-width,--print-empty,--sort-column


CTU
---

.. autoprogram-cliff:: lim
   :command: ctu *
   :ignored: -f,-c,--quote,--noindent,--max-width,--fit-width,--print-empty,--sort-column


PCAP
----

.. autoprogram-cliff:: lim
   :command: pcap *
   :ignored: -f,-c,--quote,--noindent,--max-width,--fit-width,--print-empty,--sort-column


.. _cliff: https://pypi.org/project/cliff/
.. _packet-cafe: https://www.cyberreboot.org/projects/packet-cafe/
.. _CTU Datasets: https://www.stratosphereips.org/datasets-overview

.. EOF
