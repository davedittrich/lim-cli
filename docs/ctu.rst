.. _ctu_datasets:

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

::

    $ lim ctu overview
    For an overview of the CTU Datasets, open the following URL in a browser:
    https://www.stratosphereips.org/datasets-overview

    When using this data, make sure to respect the Disclaimer at the bottom of
    the scenario ``Readme.*`` files:

    ::

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
will load the `JSON index file`_ and scrape the web pages to the capture
scenarios to extract metadata. This index and metadata are cached for a period
of time to minimize impacts on their web site.

.. _JSON index file: https://www.stratosphereips.org/blog/2021/1/4/stratosphere-datasets-update-quickly-browse-and-search

By default, the cache will be stored in your ``HOME`` directory in a file named
``.lim-ctu-cache.json`` to be shared across shells. If you need to maintain separate
caches, override this path by setting the environment variable ``LIM_CTU_CACHE``
with the path, or use the ``--cache-file`` option.

::

    $ lim ctu list -c Capture_Name -c Malware --limit 10 --elapsed
    [+] generating metadata cache '/Users/dittrich/.lim-ctu-cache.json'
    [+] queued 400 pages for processing
    +-------------------------------+-----------+
    | Capture_Name                  | Malware   |
    +-------------------------------+-----------+
    | CTU-Malware-Capture-Botnet-90 | Conficker |
    | CTU-Malware-Capture-Botnet-92 | Wootbot   |
    | CTU-Malware-Capture-Botnet-91 | Conficker |
    | CTU-Malware-Capture-Botnet-42 | Neeris    |
    | CTU-Malware-Capture-Botnet-48 | Sogou     |
    | CTU-Malware-Capture-Botnet-43 | Neeris    |
    | CTU-Malware-Capture-Botnet-44 | RBot      |
    | CTU-Malware-Capture-Botnet-45 | RBot      |
    | CTU-Malware-Capture-Botnet-46 | Virut     |
    | CTU-Malware-Capture-Botnet-54 | Virut     |
    +-------------------------------+-----------+
    [+] Elapsed time 00:00:19.36

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

::

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

::

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

::

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
