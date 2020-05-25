================
The CTU Datasets
================

One of the largest unredacted sandbox and network traffic capture datasets
available for research and experimentation are the "CTU Datasets" from the
Czech Technical University in Prague, Czech Republic.

The ``lim ctu`` subcommand group assists in searching and accessing
these datasets.

Datasets Overview
-----------------

The ``lim ctu overview`` command attempts to load the URL for the main web
page. If it can't do this, you will at least be shown the URL as seen
here.

.. code-block:: console

    $ lim ctu overview
    For an overview of the CTU Datasets, open the following URL in a browser:
    https://www.stratosphereips.org/datasets-overview

    When using this data, make sure to respect the Disclaimer at the bottom of
    the scenario ``Readme.*`` files:

    .. code-block:: console

       These files were generated in the Stratosphere Lab as part of the Malware
       Capture Facility Project in the CVUT University, Prague, Czech Republic.
       The goal is to store long-lived real botnet traffic and to generate labeled
       netflows files.

       Any question feel free to contact us:
       Sebastian Garcia: sebastian.garcia@agents.fel.cvut.cz

       You are free to use these files as long as you reference this project and
       the authors as follows:

       Garcia, Sebastian. Malware Capture Facility Project. Retrieved
       from https://stratosphereips.org

    ..

    To cite the [CTU13] dataset please cite the paper "An empirical comparison of
    botnet detection methods" Sebastian Garcia, Martin Grill, Jan Stiborek and Alejandro
    Zunino. Computers and Security Journal, Elsevier. 2014. Vol 45, pp 100-123.
    http://dx.doi.org/10.1016/j.cose.2014.05.011

..

Please respect the request in their *Disclaimer* for properly crediting them when
publishing results using this data.

Listing Scenario Data
---------------------

The first time you run a command that processes the CTU Dataset metadata, ``lim``
will scrape their web pages to extract metadata and cache it for a period of time
to minimize impact on their web site.

By default, the cache will be stored in your ``HOME`` directory in a file named
``.lim-ctu-cache.json`` to be shared across shells. If you need to maintain separate
caches, override this path by setting the environment variable ``LIM_CTU_CACHE``
with the path, or use the ``--cache-file`` option.

.. code-block:: console

    $ lim ctu list -c SCENARIO -c GROUP -c PROBABLE_NAME --limit 10 --elapsed
    [+] identifying scenarios for group mixed from https://www.stratosphereips.org/datasets-mixed
    [+] group "mixed" has 5 scenarios
    [+] identifying scenarios for group normal from https://www.stratosphereips.org/datasets-normal
    [+] group "normal" has 3 scenarios
    [+] identifying scenarios for group malware from https://www.stratosphereips.org/datasets-malware
    [+] group "malware" has 345 scenarios
    [+] identifying scenarios for group iot from https://www.stratosphereips.org/datasets-iot
    [+] group "iot" has 7 scenarios
    [+] queued 360 pages for processing
    +-------------------------------+---------+---------------+
    | SCENARIO                      | GROUP   | PROBABLE_NAME |
    +-------------------------------+---------+---------------+
    | CTU-Malware-Capture-Botnet-1  | malware | None          |
    | CTU-Malware-Capture-Botnet-2  | malware | None          |
    | CTU-Malware-Capture-Botnet-3  | malware | None          |
    | CTU-Malware-Capture-Botnet-4  | malware | PushDo        |
    | CTU-Malware-Capture-Botnet-5  | malware | None          |
    | CTU-Malware-Capture-Botnet-6  | malware | None          |
    | CTU-Malware-Capture-Botnet-7  | malware | None          |
    | CTU-Malware-Capture-Botnet-8  | malware | None          |
    | CTU-Malware-Capture-Botnet-9  | malware | None          |
    | CTU-Malware-Capture-Botnet-10 | malware | None          |
    +-------------------------------+---------+---------------+

..

.. note::

    This example only shows three columns, simply so as to fit
    the output into the space in this document. By default, there
    are many more fields and some are quite long, so generally you
    will want to add ``--fit-width`` to make the output more readable.

    .. image:: images/lim-ctu-list-fit-width.png

..


Getting Scenario Data
---------------------

The ``lim ctu get`` command is used to retrieve specific data from scenarios.
For example, you may want to get the PCAP or Netflow file from a specific
capture to extract IP addresses. Let's try to get both files for one of
the scenarios, in this case ``CTU-Malware-Capture-Botnet-113-1``:

.. code-block:: console

    $ lim --debug ctu get CTU-Malware-Capture-Botnet-113-1 LABELED PCAP
    [-] scenario "CTU-Malware-Capture-Botnet-113-1" does not have "LABELED" data: skipping
    $ tree
    .
    └── CTU-Malware-Capture-Botnet-113-1
        └── 2015-03-12_capture-win6.pcap

    1 directory, 1 file

..

As you can see, there is no ``LABELED`` data for this scenario, but we did get
the PCAP file. By default, it is put into a directory with the scenario's name
for better organization and to avoid possible file namespace clashes.

.. note::

   You can force putting files into a specific single directory by using the
   ``--data-dir`` option.

..

Alternatively, you can just specify ``ALL`` when getting data:

.. code-block:: console

    $ lim --debug -v ctu get CTU-Malware-Capture-Botnet-44 ALL --elapsed
    initialize_app
    prepare_to_run_command CTUGet
    [+] getting CTU data
    [+] cache /home/dittrich/.lim-ctu-cache.json has not yet expired
    [!] loaded metadata from cache: /home/dittrich/.lim-ctu-cache.json
    [!] downloading ZIP data for scenario CTU-Malware-Capture-Botnet-44
    [+] immediate_fetch(https://mcfp.felk.cvut.cz/publicDatasets/CTU-Malware-Capture-Botnet-44/rbot.exe.zip)
    Starting new HTTPS connection (1): mcfp.felk.cvut.cz:443
    https://mcfp.felk.cvut.cz:443 "GET /publicDatasets/CTU-Malware-Capture-Botnet-44/rbot.exe.zip HTTP/1.1" 200 108991
    [!] downloading LABELED data for scenario CTU-Malware-Capture-Botnet-44
    [+] immediate_fetch(https://mcfp.felk.cvut.cz/publicDatasets/CTU-Malware-Capture-Botnet-44/capture20110812.pcap.netflow.labeled)
    Starting new HTTPS connection (1): mcfp.felk.cvut.cz:443
    https://mcfp.felk.cvut.cz:443 "GET /publicDatasets/CTU-Malware-Capture-Botnet-44/capture20110812.pcap.netflow.labeled HTTP/1.1" 200 1506223384
    [!] downloading BINETFLOW data for scenario CTU-Malware-Capture-Botnet-44
    [+] immediate_fetch(https://mcfp.felk.cvut.cz/publicDatasets/CTU-Malware-Capture-Botnet-44/detailed-bidirectional-flow-labels/capture20110812.binetflow)
    Starting new HTTPS connection (1): mcfp.felk.cvut.cz:443
    https://mcfp.felk.cvut.cz:443 "GET /publicDatasets/CTU-Malware-Capture-Botnet-44/detailed-bidirectional-flow-labels/capture20110812.binetflow HTTP/1.1" 200 639643247
    [!] downloading PCAP data for scenario CTU-Malware-Capture-Botnet-44
    [+] immediate_fetch(https://mcfp.felk.cvut.cz/publicDatasets/CTU-Malware-Capture-Botnet-44/botnet-capture-20110812-rbot.pcap)
    Starting new HTTPS connection (1): mcfp.felk.cvut.cz:443
    https://mcfp.felk.cvut.cz:443 "GET /publicDatasets/CTU-Malware-Capture-Botnet-44/botnet-capture-20110812-rbot.pcap HTTP/1.1" 200 128575191
    [!] clean_up CTUGet
    [+] Elapsed time 00:09:06.86

..

The directory for scenario ``CTU-Malware-Capture-Botnet-44`` now has PCAP,
bidirectional netflow, bidirectional netflow with labels, and the malware
artifact in ZIP format.

.. code-block:: console

    $ tree
    .
    ├── CTU-Malware-Capture-Botnet-113-1
    │   └── 2015-03-12_capture-win6.pcap
    └── CTU-Malware-Capture-Botnet-44
        ├── botnet-capture-20110812-rbot.pcap
        ├── capture20110812.binetflow
        ├── capture20110812.pcap.netflow.labeled
        └── rbot.exe.zip

    2 directories, 5 files

..

.. EOF
