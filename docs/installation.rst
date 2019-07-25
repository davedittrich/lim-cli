============
Installation
============

This section covers installation of ``lim``.

Create a Python virtual environment
-----------------------------------

It is generally recommended to use a Python virtual environment
to isolate installation of third-party open source packages
that could potentially break the default operating system
installation of Python by accidentally upgrading incompatible
versions of necessary packages, or when packages required by
specific open source modules require a more recent version of
Python than the one installed with your operating system.  E.g.,
the `python_secrets`_ package requires Python 3.6 or newer,
while some operating systems come with Python 2.7 or Python
3.4.

Install a version of Python 3.6 (or higher) in your user
account file system space, then from the ``lim`` directory
run this version of Python with a full path, using the
following command line arguments:

.. code-block:: console

    $ /home/dittrich/miniconda3/bin/python3.6 -m venv env
    $ tree -L 1 env
    env
    ├ bin
    ├ include
    ├ lib
    ├ lib64 -> lib
    └ pyvenv.cfg

    4 directories, 1 file

..

To activate the virtual environment, source the activation script.
Many Linux shell prompts will immediately show the active
Python virtual environment as part of the shell prompt, as
seen here:

.. code-block:: console

    $ type python3
    python3 is /home/dittrich/miniconda3/bin/python3
    $ source env/bin/activate
    (env) $ type python3
    python3 is /home/dittrich/git/lim/env/bin/python3
    (env) $

..

.. note::


    It is a good idea to immediately update ``pip`` in the new
    virtual environment, just in case it was out of date.

    .. code-block:: console

        $ python3 -m pip install -U pip
        Cache entry deserialization failed, entry ignored
        Collecting pip
          Cache entry deserialization failed, entry ignored
          Downloading https://files.pythonhosted.org/packages/c2/d7/90f34cb0d83a6c5631cf71dfe64cc1054598c843a92b400e55675cc2ac37/pip-18.1-py2.py3-none-any.whl (1.3MB)
            100% |████████████████████████████████| 1.3MB 306kB/s
        Installing collected packages: pip
          Found existing installation: pip 9.0.3
            Uninstalling pip-9.0.3:
              Successfully uninstalled pip-9.0.3
        Successfully installed pip-18.1

    ..

..

Installing ``lim``
-------------------

Production use of ``lim`` should take advantage of released
versions on PyPi. Testing of development versions that have
not yet been released can be installed from the GitHub
repository's ``master`` or ``develop`` branch. Development
use (e.g., for creating pull requests with bug fixes and
new features) will generally install from a local clone of
the GitHub repository. Each of these are described below.

Production
~~~~~~~~~~

The released version of ``lim`` can be installed
using ``pip``.

.. code-block:: console

    (env) $ python -m pip install -U lim

..

Testing
~~~~~~~

Installation from the ``master`` or ``develop`` branches of
the GitHub repo can be done using ``pip``:

.. code-block:: console

    (env) $ python -m pip install -U https://github.com/LiminalAI/lim/archive/master.zip

..

... or:

.. code-block:: console


    (env) $ python -m pip install -U https://github.com/LiminalAI/lim/archive/develop.zip

..


Development
~~~~~~~~~~~

Clone the ``lim`` code repository into your Git base directory.

.. code-block:: console

    $ git clone https://github.com/LiminalAI/lim.git ~/git/lim
    Cloning into '/home/dittrich/git/lim'...
    remote: Enumerating objects: 174, done.
    remote: Counting objects: 100% (174/174), done.
    remote: Compressing objects: 100% (95/95), done.
    remote: Total 1397 (delta 102), reused 132 (delta 68), pack-reused 1223
    Receiving objects: 100% (1397/1397), 264.53 KiB | 0 bytes/s, done.
    Resolving deltas: 100% (920/920), done.
    Checking connectivity... done.
    $ cd ~/git/lim
    $ tree -L 1
    .
    ├ AUTHORS.rst
    ├ bandit.yaml
    ├ bootfreq.yml
    ├ CONTRIBUTING.rst
    ├ docs
    ├ HISTORY.rst
    ├ Makefile
    ├ MANIFEST.in
    ├ post-install.sh
    ├ README.rst
    ├ requirements.txt
    ├ setup.cfg
    ├ setup.py
    ├ test-requirements.txt
    ├ tests
    ├ tox.ini
    ├ trovares-requirements.txt
    ├ VERSION
    ├ lim
    ├ zrpattern_orig.yml
    └ zrpattern.yml

    4 directories, 18 files

..

.. note::

   There are two directories with similar names, but very different purposes.
   The directory ``lim`` is the source directory for the Cliff ``lim`` CLI
   application.  Unless otherwise specified, the current working directory for
   example commands will be the top level of the cloned directory,
   ``/home/dittrich/git/lim`` in this case.

..

After cloning the source repository, there are several steps required
to install pre-requisite software packages and to set up Terraform
and AWS access information.


Install pre-requisite software
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Required Python packages can be installed using the ``requirements.txt`` file.

.. code-block:: console

    $ python -m pip install -U -r requirements.txt
    Collecting cliff (from -r requirements.txt (line 1))
      Using cached https://files.pythonhosted.org/packages/8e/1a/5404afee3d83a2e5f27e0d20ac7012c9f07bd8e9b03d0ae1fd9bb3e63037/cliff-2.14.
    0-py2.py3-none-any.whl
    Collecting gnureadline (from -r requirements.txt (line 2))
      Downloading https://files.pythonhosted.org/packages/f5/c7/03754b54c8d0c5c5303ae2232ed36734faa91e819f0738b0d5d0a581f68c/gnureadline-
    6.3.8-cp36-cp36m-manylinux1_x86_64.whl (474kB)
        100% |████████████████████████████████| 481kB 508kB/s
    . . .
    Successfully installed MarkupSafe-1.1.0 PrettyTable-0.7.2 PyYAML-3.13 Pygments-2.3.1 alabaster-0.7.12 asn1crypto-0.24.0 attrs-18.2.0
    babel-2.6.0 bcrypt-3.1.5 certifi-2018.11.29 cffi-1.11.5 chardet-3.0.4 cliff-2.14.0 cmd2-0.9.6 colorama-0.4.1 coloredlogs-10.0 cryptog
    raphy-2.4.2 docutils-0.14 executor-21.3 fasteners-0.14.1 filelock-3.0.10 gnupg-2.3.1 gnureadline-6.3.8 humanfriendly-4.17 idna-2.8 im
    agesize-1.1.0 jinja2-2.10 lxml-4.2.5 monotonic-1.5 naturalsort-1.5.1 numpy-1.15.4 packaging-18.0 pandas-0.23.4 paramiko-2.4.2 pbr-5.1
    .1 pluggy-0.8.0 property-manager-2.3.1 psutil-5.4.8 py-1.7.0 pyasn1-0.4.4 pycparser-2.19 pynacl-1.3.0 pyparsing-2.3.0 pyperclip-1.7.0
     python-dateutil-2.7.5 python-secrets-18.11.5 pytz-2018.7 requests-2.21.0 six-1.12.0 snowballstemmer-1.2.1 sphinx-1.8.2 sphinxcontrib
    -websupport-1.1.0 sshtunnel-0.1.4 stevedore-1.30.0 toml-0.10.0 tox-3.6.1 update-dotdee-5.0 urllib3-1.24.1 verboselogs-1.7 virtualenv-
    16.1.0 wcwidth-0.1.7 xkcdpass-1.17.0 yamlreader-3.0.4

..

Other programs, like ``terraform``, may need to be installed manually.


Configure a ``python_secrets`` environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The `python_secrets`_ program is used to store secrets (e.g., an Amazon AWS
API key for a limited AWS user, passwords, etc) and other related variables
(e.g., path to SSH private key), and the ``terraform`` state files (which will
also contain copies of secrets). These variables and files are organized into
directory trees known as `environments`.  The name of the environment we want
to use for the purposes of this documentation is going to be ``lim``.

.. code-block:: console

    $ psec environments path
    /home/dittrich/.secrets/lim
    $ psec environments tree lim
    environment "lim" does not exist

..

Explicitly set the default `python_secrets environment`_ identifier for use
in the Git source repository.

.. code-block:: console

    $ pwd
    $ /home/dittrich/git/lim
    $ psec environments default lim
    default environment set to "lim"

..

Tests
-----

Testing is done using the `Bats: Bash Automated Testing System`_
testing framework.  See `Testing Your Shell Scripts, with Bats`_ for
information on setting up and using BATS.


.. _Bats\: Bash Automated Testing System: https://github.com/sstephenson/bats
.. _Testing Your Shell Scripts, with Bats: https://medium.com/@pimterry/testing-your-shell-scripts-with-bats-abfca9bdc5b9

.. _python_secrets: https://github.com/davedittrich/python_secrets
.. _python_secrets environment: https://github.com/davedittrich/python_secrets#environments
