=======
Testing
=======

*Test-driven development* improves the ability to upgrade your code
base to keep up with API changes, to refactor without incurring
regression errors, or to validate when bugs in dependent libraries
have been fixed.

Testing in ``lim`` is driven by ``tox`` from the ``Makefile`` in the
top level repo directory, using the `Bats: Bash Automated Testing System`_
testing framework.  See `Testing Your Shell Scripts, with Bats`_ for
information on setting up and using BATS.

The ``tox`` tests are performed using the following configuration file:

.. literalinclude:: ../tox.ini

.. _Bats\: Bash Automated Testing System: https://github.com/sstephenson/bats
.. _Testing Your Shell Scripts, with Bats: https://medium.com/@pimterry/testing-your-shell-scripts-with-bats-abfca9bdc5b9

There are built-in unit tests and security tests for the Python ``lim``
application, as well as runtime ``bats`` tests that perform realtime
integration or system tests.

.. note::

   The examples of output from ``bats`` and ``tox`` tests are truncated to 80
   characters and do not represent the exact output you would see if you ran
   these commands at the command line.

..


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

.. EOF
