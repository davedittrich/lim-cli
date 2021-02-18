=======
Testing
=======

*Test-driven development* improves the ability to upgrade your code
base to keep up with API changes, to refactor without incurring
regression errors, or to validate when bugs in dependent libraries
have been fixed.

Testing in ``lim`` is driven by ``tox`` from the ``Makefile`` in the
top level repo directory, using the `Bats-core: Bash Automated Testing System (2018)`_
testing framework.  See `Testing Your Shell Scripts, with Bats`_ for
information on using BATS.

.. note::

    Note that ``bats-core`` is a more recent fork of the original
    `Bats: Bash Automated Testing System`_ system, which is no longer
    being actively maintained.  ``bats-core`` has more features than
    the older ``bats`` program that may come pre-installed with your
    OS or package management system.  The tests here rely on things
    like the ``setup_file()`` function to ensure data files are
    present for runtime tests.

    The ``Makefile`` in this repo ensures that the newer ``bats-core``
    program is installed into ``/usr/local/bin`` and that related
    related libraries that are used by tests are installed locally
    in the ``tests/lib`` directory.


Run ``make help`` to see the targets associated with testing. The
primary targets are ``test`` for unit testing code, and
``test-bats-runtime`` for runtime integration testing.

The ``tox`` tests are performed using the following configuration file:

.. literalinclude:: ../tox.ini

.. _Bats\: Bash Automated Testing System: https://github.com/sstephenson/bats
.. _Bats-core\: Bash Automated Testing System (2018): https://github.com/bats-core/bats-core
.. _Testing Your Shell Scripts, with Bats: https://medium.com/@pimterry/testing-your-shell-scripts-with-bats-abfca9bdc5b9

There are built-in unit tests and security tests for the Python ``lim``
application, as well as runtime ``bats`` tests that perform realtime
integration or system tests.

.. note::

   The examples of output from ``bats`` and ``tox`` tests are truncated to 80
   characters and do not represent the exact output you would see if you ran
   these commands at the command line.

..

Data files
----------

Some of the tests require PCAP files. One of the test files
(``smallFlows_nopayloads.pcap``) comes from the Packet Café source repository.
If a clone of that directory exists at ``~/git/packet_cafe``, the file will be
copied from the local clone. Otherwise, it will be downloaded from GitHub.

Other test files come from the CTU web server and are downloaded as needed
(using ``lim``, of course.)


Unit tests
----------

Invoke unit tests with the helper ``Makefile`` using the ``test``
target (e.g., ``make test``). This target runs ``tox`` tests for the Python code
(``make test-tox``), followed by some basic unit tests performed with
``bats`` (``make test-bats``).

If successful, you will see the following:

.. literalinclude:: test-tox.txt

Immediately following this are the ``bats`` unit tests. Successful results
will look like this:

.. literalinclude:: test-bats.txt


Integration tests
-----------------

The integration and system tests using ``bats`` require a live network
connection and/or a running `packet-cafe`_ server.  Because of this,
these tests are only run on demand and not as part of basic unit
testing and code analysis.


The ``bats`` tests can then be run using the helper ``Makefile`` target
``test-bats-runtime``.

.. literalinclude:: test-bats-runtime.txt


.. _packet-cafe: https://www.cyberreboot.org/projects/packet-cafe/

Writing and debugging BATS tests
--------------------------------

Files that are used by tests are loaded into the directory pointed
to by the runtime environment variable ``BATS_RUN_TMPDIR``. This is
to avoid cluttering up the repo directory with temporary files.
This directory is removed on exit (see `source code`_).

.. _source code: https://github.com/bats-core/bats-core/blob/290504056fe6187e28c829d8ae3e2c8d7f143ec8/libexec/bats-core/bats

To see the values of these variables, place the following command
in the ``.bats`` file and run it with the ``-t`` flag::

    env | grep BATS_ >&3

The output will expose the runtime values::

    $ bats -t tests/runtime_30_packet_cafe.bats
    1..39
    BATS_ROOT_PID=55272
    BATS_TEST_SOURCE=/Users/dittrich/tmp/bats-run-55272/bats.55345.src
    BATS_TMPDIR=/Users/dittrich/tmp
    BATS_RUN_TMPDIR=/Users/dittrich/tmp/bats-run-55272
    BATS_VERSION=1.2.1
    BATS_TEST_PATTERN=^[[:blank:]]*@test[[:blank:]]+(.*[^[:blank:]])[[:blank:]]+\{(.*)$
    BATS_CWD=/Users/dittrich/git/LiminalInfo/lim-cli
    BATS_TEMPDIR_CLEANUP=1
    BATS_TEST_FILTER=
    BATS_TEST_PATTERN_COMMENT=[[:blank:]]*([^[:blank:]()]+)[[:blank:]]*\(?\)?[[:blank:]]+\{[[:blank:]]+#[[:blank:]]*@test[[:blank:]]*$
    BATS_LIBEXEC=/usr/local/libexec/bats-core
    BATS_ROOT=/usr/local
    not ok 1 setup_file failed
    # (from function `setup_file' in test file tests/runtime_30_packet_cafe.bats, line 25)
    #   `echo "Packet Cafe containers are not running ('lim cafe docker up'?)" >&2' failed
    # [-] packet-cafe containers are not running
    # Packet Cafe containers are not running ('lim cafe docker up'?)
    # bats warning: Executed 1 instead of expected 39 tests


.. EOF
