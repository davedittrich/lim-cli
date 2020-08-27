# -*- coding: utf-8 -*-

import asyncio
import datetime
import os
import pathlib
import platform
import pbr.version
import sys
import textwrap

# PBR has a bug that produces incorrect version numbers
# if you run ``psec --version`` in another Git repo.
# This attempted workaround only uses PBR for getting
# version and revision number if run in a directory
# path that contains strings that appear to be
# a python_secrets repo clone.

p = pathlib.Path(os.getcwd())
if 'lim-cli' in p.parts or 'lim' in p.parts:
    try:
        version_info = pbr.version.VersionInfo('lim')
        __version__ = version_info.cached_version_string()
        __release__ = version_info.release_string()
    except Exception:
        pass
else:
    __version__ = '20.8.7'
    __release__ = __version__

BUFFER_SIZE = 128 * 1024
DAY = os.environ.get('DAY', 5)
DEFAULT_PROTOCOLS = ['icmp', 'tcp', 'udp']
KEEPALIVE = 5.0
LIM_DATA_DIR = os.environ.get('LIM_DATA_DIR', os.getcwd())
MAX_LINES = None
MAX_ITEMS = 10
# Use syslog for logging?
# TODO(dittrich): Make this configurable, since it can fail on Mac OS X
SYSLOG = False

__author__ = 'Dave Dittrich'
__email__ = 'dave.dittrich@gmail.com'


def copyright():
    """Copyright string"""
    this_year = datetime.datetime.today().year
    copyright = textwrap.dedent(
        f"""Author:    Dave Dittrich <dave.dittrich@gmail.com>
        Copyright: 2018-{ this_year }, Dave Dittrich. 2019-{ this_year }, Liminal Information Corp.
        License:   Apache 2.0 License
        URL:       https://pypi.python.org/pypi/lim-cli""")  # noqa
    return copyright


def stdout_callback(x):
    """Default callback processor for stdout stream."""
    sys.stdout.write(x.decode('utf-8'))
    sys.stdout.flush()


def stderr_callback(x):
    """Default callback processor for stderr stream."""
    sys.stderr.write(x.decode('utf-8'))
    sys.stdout.flush()


async def _read_stream(stream, cb):
    """Subprocess stream reader coroutine."""
    while True:
        line = await stream.readline()
        if line:
            cb(line)
        else:
            break


async def _stream_subprocess(
    cmd,
    env=None,
    cwd=os.getcwd(),
    stdout_cb=None,
    stderr_cb=None
):
    """Process stdout and sterr streams using coroutines."""
    process = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=cwd,
        env=env,
        limit=2**20,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await asyncio.wait([
        _read_stream(process.stdout, stdout_cb),
        _read_stream(process.stderr, stderr_cb)
    ])
    await process.communicate()
    return await process.wait()


def execute(
    cmd,
    cwd=None,
    env=None,
    stdout_cb=stdout_callback,
    stderr_cb=stderr_callback
):
    """Execute a command and pass along stdout/stderr in realtime."""

    if asyncio.get_event_loop().is_closed():
        asyncio.set_event_loop(asyncio.new_event_loop())
    if platform.system() == "Windows":
        asyncio.set_event_loop(asyncio.ProactorEventLoop())
    loop = asyncio.get_event_loop()
    rc = loop.run_until_complete(
        _stream_subprocess(
            cmd,
            cwd=cwd,
            env=env,
            stdout_cb=stdout_cb,
            stderr_cb=stderr_cb,
        )
    )
    loop.close()
    return rc


# Test for the asyncio subprocess code
if __name__ == '__main__':
    print(
        execute(
            [
                "bash",
                "-c",
                "echo stdout && sleep 1 && echo stderr 1>&2 && sleep 1 && echo done"  # noqa
            ],
            stdout_cb=lambda x: sys.stderr.write(f"STDOUT: {x.decode('utf-8')}"),  # noqa
            stderr_cb=lambda x: sys.stderr.write(f"STDERR: {x.decode('utf-8')}"),  # noqa
        )
    )


# vim: set ts=4 sw=4 tw=0 et :
