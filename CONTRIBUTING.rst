============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

You can contribute in many ways:

Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/LiminalInfo/lim/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug"
is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "feature"
is open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

`lim` could always use more documentation, whether as part of the
official docs, in docstrings, or even on the web in blog posts,
articles, and such.

Documentation includes comments in source code. Sphinx is used to
produce some of the documentation for `lim` from source code itself.
Follow the `Google Python Style Guide`_, for example its guidance
on use of `comments and docstrings`_.

.. _Google Python Style Guide: https://google.github.io/styleguide/pyguide.html
.. _comments and docstrings: https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings


Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at https://github.com/LiminalInfo/lim/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

Get Started!
------------

Ready to contribute? Here's how to set up `lim` for local development.

1. Fork the `lim` repo on GitHub.
2. Clone your fork locally::

    $ git clone git@github.com:your_name_here/lim-cli.git

3. Install your local copy into a virtualenv. Assuming you have virtualenvwrapper installed, this is how you set up your fork for local development::

    $ mkvirtualenv lim
    $ cd lim/
    $ python setup.py develop

   If you are using an IDE like Visual Studio Code, and you want to add new subcommands
   in the `setup.py` file, you will need to install the package into the virtualenv first
   in order for `cliff` to dynamically load the functions. Run `make install-active` to do
   this. You can then run the debugger and the new subcommands will load properly.

4. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

5. When you're done making changes, check that your changes pass `flake8`, `bandit`, and other tests including testing other Python versions with `tox`::

    $ make test

6. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

7. Submit a pull request through the GitHub website.

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a `cliff`` class with a docstring and epilog
   text and/or add the feature description to the list in `README.rst`.
3. The pull request should work for the environments listed in `tox.ini`.Check
   https://travis-ci.org/LiminalInfo/lim/pull_requests
   and make sure that the tests pass for all supported Python versions.

Tips
----

To run all tests, simply do ``make test``.

To run a subset of tests for more fine grained development testing,
do something like this::

    $ workon lim
    $ python -m unittest tests.test_ctu
    ........................
    ----------------------------------------------------------------------
    Ran 24 tests in 0.519s

    OK
