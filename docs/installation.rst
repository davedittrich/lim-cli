============
Installation
============

This section covers installation of ``lim``.

Production use of ``lim`` should take advantage of released
versions on PyPi. Testing of development versions that have
not yet been released can be installed from the GitHub
repository's ``master`` or ``develop`` branch. Development
use (e.g., for creating pull requests with bug fixes and
new features) will generally install from a local clone of
the GitHub repository. Each of these are described below.

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

There are two ways to handle this situation.

1. If you intend on doing development and testing of the
   ``lim`` Python source code itself, it is best to use
   a Python virtual environment that you maintain manually.
   This is a little more complicated, but you will find it
   better suited for development.

2. If you simply need to run the ``lim`` CLI on an analysis
   workstation in a "production" sense, there is an
   easier way to manage the virtual environment and package
   installation more like you would with an operating system
   package manager.

The second, simpler method, will be covered first.

Production (non-development) installation
-----------------------------------------

The program ``pipx`` is the easiest way to install a Python package
including command line scripts to run them as stand-alone commands
in their own virtual environments (without having to know much about
virtual environments). Programs installed by ``pipx`` are called
*apps*.

``pipx`` manages creating the virtual environment and creating links to a
common runtime directory that you add to your ``$PATH`` to run them.

On a Mac running Darwin, Homebrew is the easiest way to install
``pipx``:

::

    $ brew info pipx
    pipx: stable 0.15.4.0 (bottled), HEAD
    Execute binaries from Python packages in isolated environments
    https://github.com/pipxproject/pipx
    /usr/local/Cellar/pipx/0.15.4.0 (125 files, 660.3KB) *
      Poured from bottle on 2020-05-27 at 10:21:20
    From: https://github.com/Homebrew/homebrew-core/blob/master/Formula/pipx.rb
    ==> Dependencies
    Required: python@3.8 ✔
    ==> Options
    --HEAD
        Install HEAD version
    ==> Analytics
    install: 2,090 (30 days), 4,963 (90 days), 8,568 (365 days)
    install-on-request: 2,093 (30 days), 4,963 (90 days), 8,553 (365 days)
    build-error: 0 (30 days)

Install ``pipx`` as follows:

.. code-block:: console

    $ brew install pipx
    Updating Homebrew...
    ==> Auto-updated Homebrew!
    ==> Downloading https://homebrew.bintray.com/bottles/pipx-0.15.4.0.mojave.bottle.tar.gz
    Already downloaded: /Users/dittrich/Library/Caches/Homebrew/downloads/6251803fbe228622581468fc08e6f781172e7083c958e424693b471cb1953d1c--pipx-0.15.4.0.mojave.bottle.tar.gz
    ==> Pouring pipx-0.15.4.0.mojave.bottle.tar.gz
    🍺  /usr/local/Cellar/pipx/0.15.4.0: 92 files, 530.9KB

Now install ``lim`` as an app using the package name ``lim-cli``.

.. code-block:: console

    $ pipx install lim-cli
      installed package lim-cli 20.5.2, Python 3.8.2
      These apps are now globally available
        - lim
    done! ✨ 🌟 ✨

You can get information about the path where apps are located,
the parent package name and current release version,
the version of Python the apps use, the apps (scripts)
installed from the parent package name, etc.

.. code-block:: console

    $ pipx list
    venvs are in /Users/dittrich/.local/pipx/venvs
    apps are exposed on your $PATH at /Users/dittrich/.local/bin
       package ansible 2.9.9, Python 3.8.2
        - ansible
        - ansible-config
        - ansible-connection
        - ansible-console
        - ansible-doc
        - ansible-galaxy
        - ansible-inventory
        - ansible-playbook
        - ansible-pull
        - ansible-test
        - ansible-vault
       package asciinema 2.0.2, Python 3.8.2
        - asciinema
       package blockdiag 2.0.1, Python 3.8.2
        - blockdiag
       package bump2version 1.0.0, Python 3.8.2
        - bump2version
        - bumpversion
       package lim-cli 20.5.2, Python 3.8.2
        - lim
       package sphinx 3.0.4, Python 3.8.2
        - sphinx-apidoc
        - sphinx-autogen
        - sphinx-build
        - sphinx-quickstart
       package twine 3.1.1, Python 3.8.2
        - twine

For more information on capabilities of ``pipx``, see
the project web site: https://github.com/pipxproject/pipx


Development and testing installation
------------------------------------

Source directory setup
~~~~~~~~~~~~~~~~~~~~~~

Start by cloning the ``lim`` code repository into your Git base
directory.

.. code-block:: console

    $ git clone https://github.com/davedittrich/lim-cli.git ~/git/lim-cli
    Cloning into '/home/dittrich/git/lim-cli'...
    remote: Enumerating objects: 174, done.
    remote: Counting objects: 100% (174/174), done.
    remote: Compressing objects: 100% (95/95), done.
    remote: Total 1397 (delta 102), reused 132 (delta 68), pack-reused 1223
    Receiving objects: 100% (1397/1397), 264.53 KiB | 0 bytes/s, done.
    Resolving deltas: 100% (920/920), done.
    Checking connectivity... done.
    $ cd ~/git/lim-cli
    $ tree -L 1
    .
    ├── AUTHORS
    ├── AUTHORS.rst
    ├── CONTRIBUTING.rst
    ├── ChangeLog
    ├── HISTORY.rst
    ├── LICENSE-2.0.txt
    ├── MANIFEST.in
    ├── Makefile
    ├── README.rst
    ├── VERSION
    ├── bandit.yaml
    ├── docs
    ├── lim
    ├── requirements.txt
    ├── setup.cfg
    ├── setup.py
    ├── test-requirements.txt
    ├── tests
    └── tox.ini

    3 directories, 16 files

..

.. note::

   There is a subdirectory with the same name as the top level directory.
   The directory ``lim-cli`` is the source directory for the Cliff ``lim`` CLI
   application.  Unless otherwise specified, the current working directory for
   example commands will be the top level of the cloned directory,
   ``/home/dittrich/git/lim-cli`` in this case.

..

Within this source directory, you can then create a virtual environment
using a version of Python 3.6 (or higher):

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

To activate this virtual environment, source the activation script.
Many Linux shell prompts will immediately show the active
Python virtual environment as part of the shell prompt, as
seen here:

.. code-block:: console

    $ type python3
    python3 is /home/dittrich/miniconda3/bin/python3
    $ source env/bin/activate
    (env) $ type python3
    python3 is /home/dittrich/git/lim-cli/env/bin/python3
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
          Downloading https://files.pythonhosted.org/packages/.../pip-20.1-py2.py3-none-any.whl (1.5 MB)
            100% |████████████████████████████████| 1.3MB 306kB/s
        Installing collected packages: pip
          Attempting uninstall: pip
            Found existing installation: pip 19.3.1
            Uninstalling pip-19.3.1:
              Successfully uninstalled pip-19.3.1
        Successfully installed pip-20.1

    ..

..

After cloning the source repository, there are several steps required
to install ``lim`` and its pre-requisite software packages.


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
    $ /home/dittrich/git/lim-cli
    $ psec environments default lim
    default environment set to "lim"

..

.. note::

   There is a irritating side-effect of using Cliff, which loads commands dynamically
   using the Python ``setup.py`` packaging mechanism. You can't just use the
   normal Python ``setup.py develop`` mechanism to run code directly from the
   current working directory. You need to install the full package into the
   current Python environment with ``make install-active`` and then the ``lim``
   app will load the current versions of commands properly.

   There may be another way to do this, but it isn't obvious and hasn't been
   identified yet. This mechanism, though a little tedious, does work.

..

To update the user documentation as you code--you do document your code well,
right? right?--you can either build the Sphinx documentation as part of the
``make test`` tasks (one of which is testing Sphinx generation), or you
can do it manually with ``make docs``.

.. code-block:: console

    $ make docs
    (cd docs && make clean html)
    rm -rf _build/*
    sphinx-build -b html -d _build/doctrees   . _build/html
    Running Sphinx v2.1.2
    making output directory... done
    building [mo]: targets for 0 po files that are out of date
    building [html]: targets for 8 source files that are out of date
    updating environment: 8 added, 0 changed, 0 removed
    reading sources... [100%] usage
    looking for now-outdated files... none found
    pickling environment... done
    checking consistency... done
    preparing documents... done
    writing output... [100%] usage
    generating indices... genindex
    writing additional pages... search
    copying static files... done
    copying extra files... done
    dumping search index in English (code: en) ... done
    dumping object inventory... done
    build succeeded, 5 warnings.

    The HTML pages are in _build/html.

    Build finished. The HTML pages are in _build/html.

..

If you are on a Mac, you can then open the document in your default browser with
``open docs/_build/html/index.html``.


.. _python_secrets: https://github.com/davedittrich/python_secrets
.. _python_secrets environment: https://github.com/davedittrich/python_secrets#environments
