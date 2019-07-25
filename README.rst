===
lim
===

.. .. image:: https://img.shields.io/pypi/v/lim.svg
..         :target: https://pypi.python.org/pypi/lim
..
.. .. image:: https://img.shields.io/travis/LiminalAI/lim.svg
..         :target: https://travis-ci.org/LiminalAI/lim
..
.. .. image:: https://readthedocs.org/projects/lim/badge/?version=latest
..         :target: https://lim.readthedocs.io/en/latest/?badge=latest
..         :alt: Documentation Status


Python CLI for LiminalAI.

* License: Apache 2.0 License
* Documentation: https://lim.readthedocs.io/en/latest/


Features
--------

* Uses the `openstack/cliff`_ command line framework.

.. _openstack/cliff: https://github.com/openstack/cliff

Usage information for subcommands is available in the **Usage** section.
This section covers high-level concepts related to the ``lim`` app.

Output formatting
-----------------

One of the benefits of the Cliff framework is the ability to switch from the
table output seen earlier to another output format, such as JSON, CSV, or in
certain cases even shell variable definitions.  This helps generalize and
abstract out into data structures a mechanism to handle the coupling of
internal program variable names between multiple programs. Rather than
hard-coding, the template can be used to define the variables and values for a
given program run.

.. Here are examples of the JSON and CSV output:
.. 
.. .. code-block:: console
.. 
..     $ lim query show vars zrpattern -f json
..     [
..       {
..         "variable": "port",
..         "description": "Port number",
..         "type": "int",
..         "default": 3128,
..         "substitute": ""
..       },
..       {
..         "variable": "threshold",
..         "description": "Threshold in seconds",
..         "type": "int",
..         "default": 3,
..         "substitute": "actThresh"
..       },
..       {
..         "variable": "duration",
..         "description": "Duration in seconds",
..         "type": "int",
..         "default": 3600,
..         "substitute": "mindur"
..       }
..     ]
..     $ lim query show vars zrpattern -f csv
..     "variable","description","type","default","substitute"
..     "port","Port number","int",3128,""
..     "threshold","Threshold in seconds","int",3,"actThresh"

.. EOF
