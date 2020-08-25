# -*- coding: utf-8 -*-

import argparse
import logging
import os
import sys
import textwrap

from cliff.command import Command
from cliff.lister import Lister
from lim import execute
from lim.packet_cafe import add_docker_global_options
from lim.packet_cafe import add_packet_cafe_global_options
from lim.packet_cafe import containers_are_running
from lim.packet_cafe import get_containers
from lim.packet_cafe import get_images
from lim.packet_cafe import get_output
from lim.packet_cafe import rm_images
from lim.packet_cafe import Packet_Cafe


logger = logging.getLogger(__name__)

RUNNING_MSG = '[-] packet-cafe containers are already running'
NOT_RUNNING_MSG = '[-] packet-cafe containers are not running'


def print_output(results=[]):
    for line in results:
        sys.stdout.write(line)
        if '\x1b' not in line:
            sys.stdout.write('\n')


def get_environment(args):
    env = os.environ.copy()
    if args.docker_service_namespace is not None:
        env["SERVICE_NAMESPACE"] = args.docker_service_namespace
    if args.docker_service_version is not None:
        env["SERVICE_VERSION"] = args.docker_service_version
    if args.docker_tool_namespace is not None:
        env["TOOL_NAMESPACE"] = args.docker_tool_namespace
    if args.docker_tool_version is not None:
        env["TOOL_VERSION"] = args.docker_tool_version
    env["REPO_DIR"] = args.packet_cafe_repo_dir
    env["GITHUB_URL"] = args.packet_cafe_github_url
    return env


def ensure_clone(url=None, repo_dir=None, branch='master'):
    """Make sure that a clone of packet_cafe exists in repo_dir."""
    if url is None:
        url = Packet_Cafe.CAFE_GITHUB_URL
    if os.path.exists(repo_dir):
        if not os.path.exists(os.path.join(repo_dir, '.git')):
            raise RuntimeError(f'[-] Directory "{repo_dir}" does not '
                               'look like a Git repository clone')
        elif not os.path.exists(os.path.join(repo_dir, 'docker-compose.yml')):
            raise RuntimeError(f'[-] Directory "{repo_dir}" does not '
                               'contain a docker-compose.yml file')
        try:
            remotes = get_remote(repo_dir)
        except RuntimeError:
            remotes = []
        if 'origin' not in remotes:
            raise RuntimeError(f'[-] Directory "{repo_dir}" does not '
                               'have a remote "origin" defined')
    else:
        logger.info(f'[-] Directory "{repo_dir}" does not exist')
        clone(url=url, repo_dir=repo_dir, branch=branch)
    return True


def clone(url=None, repo_dir=None, branch='master'):
    """Clone Git repository."""
    # $ git clone https://github.com/iqtlabs/packet_cafe.git /tmp/packet_cafe
    # Cloning into '/tmp/packet_cafe'...
    # remote: Enumerating objects: 3999, done.
    # remote: Total 3999 (delta 0), reused 0 (delta 0), pack-reused 3999
    # Receiving objects: 100% (3999/3999), 13.71 MiB | 1.67 MiB/s, done.
    # Resolving deltas: 100% (2380/2380), done.
    logger.info(f'[+] Cloning from URL {url}')
    sys.stdout.write('[+] ')
    sys.stdout.flush()
    clone_result = execute(cmd=['git', 'clone', url, repo_dir])
    if clone_result != 0:
        try:
            os.rmdir(path)
        except OSError:
            pass
        raise RuntimeError('[-] cloning failed')
    up_to_date = checkout(repo_dir, branch=branch)
    return up_to_date


def update_available(
    repo_dir=None,
    branch='master',
    remote='origin'
):
    """Check to see if GitHub repo is up to date."""
    remotes = get_remote(repo_dir)
    if len(remotes) > 1:
        others = ",".join(remotes)
        logger.info(f'[-] more than one remote found: {others}')
    if repo_dir is None:
        raise RuntimeError('[-] repo_dir must be specified')
    fetched_new = fetch(repo_dir, remote=remote)
    if fetched_new:
        logger.info('[+] fetch recieved new content')
    current_branch = get_branch(repo_dir)
    if current_branch != branch:
        raise RuntimeError(f'[-] branch "{current_branch}" is checked out')
    up_to_date = checkout(repo_dir, branch=branch)
    if not up_to_date:
        logger.info(f'[!] The branch "{branch}" is not up to date')
    # results = pull(repo_dir, remote=remote, branch=branch)
    return not up_to_date


def get_branch(repo_dir):
    """Return the name of the checked out branch."""
    results = get_output(cmd=['git', 'branch'],
                         cwd=repo_dir)
    branches = [row[2:] for row in results if row.startswith('* ')]
    if len(branches) != 1:
        raise RuntimeError('[-] failed to identify checked out branch')
    return branches[0]


def get_remote(repo_dir):
    """Return the remotes for this repo."""
    remotes = get_output(cmd=['git', 'remote'],
                         cwd=repo_dir)
    if not len(remotes):
        raise RuntimeError('[-] failed to get remotes')
    return remotes


def fetch(repo_dir, remote='origin'):
    """Fetch from remote."""
    # $ git fetch upstream
    # remote: Enumerating objects: 2, done.
    # remote: Counting objects: 100% (2/2), done.
    # remote: Compressing objects: 100% (2/2), done.
    # remote: Total 2 (delta 0), reused 0 (delta 0), pack-reused 0
    # Unpacking objects: 100% (2/2), 1.57 KiB | 1.57 MiB/s, done.
    # From https://github.com/iqtlabs/packet_cafe
    #   152ec36..cc895f5  master     -> upstream/master
    results = get_output(cmd=['git', 'fetch', remote],
                         cwd=repo_dir)
    return bool(len(results))


def checkout(repo_dir, branch='master'):
    """Checkout branch."""
    # $ git checkout master
    # Switched to branch 'master'
    # Your branch is up to date with 'origin/master'.
    # $ git checkout master
    # Already on 'master'
    # Your branch is up to date with 'origin/master'.
    results = get_output(cmd=['git', 'checkout', branch],
                         cwd=repo_dir)
    results_str = " ".join(results)
    return results_str.find('Your branch is up to date') > 0


def pull(repo_dir, remote='origin', branch='master'):
    """Return the remotes for this repo."""
    # $ git pull upstream master
    # From https://github.com/CyberReboot/packet_cafe
    # * branch            master     -> FETCH_HEAD
    # Successfully rebased and updated refs/heads/master.
    # $ git pull upstream master
    # From https://github.com/CyberReboot/packet_cafe
    # * branch            master     -> FETCH_HEAD
    # Already up to date.
    results = get_output(cmd=['git',
                              'pull',
                              f"'{remote}'",
                              f"'{branch}'"
                              ],
                         cwd=repo_dir)
    results_str = " ".join(results)
    if not (
        results_str.find('Successfully') or
        results_str.find('Already up to date')
    ):
        raise RuntimeError(
            f'[-] pull from "{remote}" to branch "{branch}" had problems')
    return True


class ContainersBuild(Command):
    """Build Packet Café Docker containers."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '-u', '--update',
            action='store_true',
            dest='update',
            default=False,
            help=('Update the repository contents before rebuilding '
                  '(default: False)')
        )
        # Text here also copied to docs/packet_cafe.rst
        parser.epilog = textwrap.dedent("""
            Build images from source locally rather than pulling them from Docker Hub.
            This is used for local deployment or development and testing locally. If
            you wish to use images from Docker Hub, use ``lim cafe containers pull``
            instead.

            You will be notified if the GitHub repo has newer content and the program
            will exit. Use the ``--update`` flag to update the repo before building.
            """)  # noqa
        return add_docker_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] locally build Packet Café Docker containers')
        if containers_are_running():
            if bool(self.app_args.verbose_level):
                logger.info(RUNNING_MSG)
            sys.exit(1)
        repo_dir = parsed_args.packet_cafe_repo_dir
        # TODO(dittrich): Fix this
        remote = "origin"
        branch = parsed_args.packet_cafe_repo_branch
        ensure_clone(url=parsed_args.packet_cafe_github_url,
                     repo_dir=repo_dir,
                     branch=branch)
        if update_available(repo_dir, remote=remote, branch=branch):
            if parsed_args.update:
                pull(repo_dir, remote=remote, branch=branch)
            else:
                raise RuntimeError(
                    f'[-] An update is available from remote "{remote}"\n'
                    '[-] Use ``-update`` to pull before building')
        elif parsed_args.update:
            logger.info('[-] No updates available')
        if self.app_args.verbose_level > 0:
            logger.info(
                f'[+] Running "docker-compose up --build" in {repo_dir}')
        # Ensure VOL_PREFIX environment variable is set
        os.environ['VOL_PREFIX'] = self.app_args.packet_cafe_data_dir
        env = get_environment(parsed_args)
        #
        # ERROR: for messenger  Get https://registry-1.docker.io/v2/davedittrich/packet_cafe_messenger/manifests/sha256:...: proxyconnect tcp: dial tcp 192.168.65.1:3129: i/o timeout  # noqa
        #
        env['COMPOSE_HTTP_TIMEOUT'] = '200'
        cmd = [
            'docker-compose',
            'up'
        ]
        if self.app_args.verbose_level <= 1:
            cmd.append('-d')
        cmd.append('--build')
        result = execute(cmd=cmd,
                         cwd=repo_dir,
                         env=env
        )
        if result != 0:
            raise RuntimeError('[-] docker-compose build failed')


class ContainersDown(Command):
    """Bring down Packet Café Docker containers."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        # Text here also copied to docs/packet_cafe.rst
        parser.epilog = textwrap.dedent("""
            Bring down the container stack associated with Packet Café services.
            """)  # noqa
        return add_docker_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] bring down Packet Café Docker containers')
        if not containers_are_running():
            if bool(self.app_args.verbose_level):
                logger.info(NOT_RUNNING_MSG)
            sys.exit(1)
        repo_dir = parsed_args.packet_cafe_repo_dir
        ensure_clone(url=parsed_args.packet_cafe_github_url,
                     repo_dir=repo_dir,
                     branch=parsed_args.packet_cafe_repo_branch)
        if self.app_args.verbose_level > 0:
            logger.info(f'[+] Running "docker-compose down" in {repo_dir}')
        cmd = ['docker-compose']
        if self.app_args.verbose_level > 1:
            cmd.append('--verbose')
        cmd.append('down')
        result = execute(
            cmd=cmd,
            cwd=repo_dir,
            env=get_environment(parsed_args)
        )
        if result != 0:
            raise RuntimeError('[-] docker-compose down failed')


class ContainersImages(Lister):
    """List Packet Café related Docker images."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '--rm',
            action='store_true',
            dest='rm_images',
            default=False,
            help='Remove the images from Docker (default: False)'
        )
        # Text here also copied to docs/packet_cafe.rst
        parser.epilog = textwrap.dedent("""
            List the images associated with Packet Café services and workers.
            """)  # noqa
        return add_docker_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] list Packet Café Docker images')
        # cmd = [
        #     'docker',
        #     'images',
        #     f'--filter=reference="{parsed_args.docker_service_namespace}/*"',
        #     f'--filter=reference="{parsed_args.docker_tool_namespace}/*"',
        #     '--format',
        #     '"table {{.ID}}\t{{.Repository}}\t{{.Tag}}"'
        # ]
        # if result != 0:
        #     raise RuntimeError('[-] failed to list containers')
        service_namespace = parsed_args.docker_service_namespace
        if service_namespace is None:
            service_namespace = 'iqtlabs'
        tool_namespace = parsed_args.docker_tool_namespace
        if tool_namespace is None:
            tool_namespace = 'iqtlabs'
        images = get_images(filter=[service_namespace, tool_namespace])
        image_set = (
            f'service namespace "{service_namespace}", '
            f'tool namespace "{tool_namespace}"'
        )
        if not len(images):
            raise RuntimeError(f'[-] no images found for {image_set}')
        if self.app_args.verbose_level > 0:
            action = 'Removing' if parsed_args.rm_images else 'Listing'
            logger.info(f'[+] {action} images for {image_set}')
        if parsed_args.rm_images:
            columns = ('ID', 'Repository')
            data = ((i['ID'], i['Repository']) for i in rm_images(images))
        else:
            columns = images[0].keys()
            data = ((i.values()) for i in images)
        return columns, data


class ContainersPull(Command):
    """Pull Packet Café Docker containers."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '-u', '--update',
            action='store_true',
            dest='update',
            default=False,
            help=('Update the repository contents before pulling '
                  '(default: False)')
        )
        # Text here also copied to docs/packet_cafe.rst
        parser.epilog = textwrap.dedent("""
            Pull the containers associated with Packet Café services and workers from
            Docker Hub to cache them locally.
            """)  # noqa
        return add_docker_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] pull Packet Café Docker containers')
        if containers_are_running():
            if bool(self.app_args.verbose_level):
                logger.info(RUNNING_MSG)
            sys.exit(1)
        env = get_environment(parsed_args)
        repo_dir = parsed_args.packet_cafe_repo_dir
        # TODO(dittrich): Fix this
        remote = "origin"
        branch = parsed_args.packet_cafe_repo_branch
        ensure_clone(url=parsed_args.packet_cafe_github_url,
                     repo_dir=repo_dir,
                     branch=branch)
        if update_available(repo_dir, remote=remote, branch=branch):
            if parsed_args.update:
                pull(repo_dir, remote=remote, branch=branch)
            else:
                raise RuntimeError(
                    f'[-] An update is available from remote "{remote}"\n'
                    '[-] Use ``-update`` to pull before building')
        if self.app_args.verbose_level > 0:
            logger.info(f'[+] Running "docker-compose pull" in {repo_dir}')
        # Ensure VOL_PREFIX environment variable is set
        os.environ['VOL_PREFIX'] = self.app_args.packet_cafe_data_dir
        env = get_environment(parsed_args)
        #
        # ERROR: for messenger  Get https://registry-1.docker.io/v2/davedittrich/packet_cafe_messenger/manifests/sha256:...: proxyconnect tcp: dial tcp 192.168.65.1:3129: i/o timeout  # noqa
        #
        env['COMPOSE_HTTP_TIMEOUT'] = '200'
        result = execute(
            cmd=['docker-compose', 'pull'],
            cwd=repo_dir,
            env=env
        )
        if result != 0:
            raise RuntimeError('[-] failed to pull containers')


class ContainersShow(Lister):
    """Show status of Packet Café Docker containers."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        # Text here also copied to docs/packet_cafe.rst
        parser.epilog = textwrap.dedent("""
            Produces a table listing the Docker containers associated with
            Packet Café (by virtue of the ``com.docker.compose.project``
            label being set to ``packet_cafe``).

            .. code-block:: console

                $ lim cafe containers show
                +-------------------------+------------+--------------------------------------+---------+
                | name                    | short_id   | image                                | status  |
                +-------------------------+------------+--------------------------------------+---------+
                | packet_cafe_messenger_1 | ce4eed9e01 | iqtlabs/packet_cafe_messenger:latest | running |
                | packet_cafe_workers_1   | 43fff494f6 | iqtlabs/packet_cafe_workers:latest   | running |
                | packet_cafe_ui_1        | 794eb87ed6 | iqtlabs/packet_cafe_ui:latest        | running |
                | packet_cafe_web_1       | a1f8f5f7cc | iqtlabs/packet_cafe_web:latest       | running |
                | packet_cafe_mercury_1   | 882b12e31f | iqtlabs/mercury:v0.11.10             | running |
                | packet_cafe_ncapture_1  | 5b1b10f3e0 | iqtlabs/ncapture:v0.11.10            | running |
                | packet_cafe_admin_1     | 73304f16cf | iqtlabs/packet_cafe_admin:latest     | running |
                | packet_cafe_redis_1     | c893c408b5 | iqtlabs/packet_cafe_redis:latest     | running |
                | packet_cafe_lb_1        | 4530125e8e | iqtlabs/packet_cafe_lb:latest        | running |
                +-------------------------+------------+--------------------------------------+---------+

            ..

            To just get a return value (``0`` for "all running" and ``1`` if not),
            use the ``-q`` option.

            .. code-block:: console

                $ lim -q cafe containers show
                $ echo $?
                0
            ..
            """)  # noqa
        return add_packet_cafe_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] show status on Packet Café Docker containers')
        if not containers_are_running():
            if bool(self.app_args.verbose_level):
                logger.info(NOT_RUNNING_MSG)
            sys.exit(1)
        elif not bool(self.app_args.verbose_level):
            sys.exit(0)
        # client = docker.from_env()
        # container_ids = [getattr(c, 'id') for c in client.containers.list()]
        columns = ['name', 'short_id', 'image', 'status']
        data = get_containers(columns=columns)
        return columns, data


class ContainersUp(Command):
    """Bring up Packet Café Docker containers."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '-u', '--update',
            action='store_true',
            dest='update',
            default=False,
            help=('Update the repository contents before rebuilding '
                  '(default: False)')
        )
        # Text here also copied to docs/packet_cafe.rst
        parser.epilog = textwrap.dedent("""
            Brings up the container and network stack associated with Packet Café
            services and workers if they are not yet running. Messages from
            ``docker-compose`` will be output to show progress. This can be
            suppressed with the ``-q`` flag.

            .. code-block:: console

                $ lim cafe containers up
                [+] Running "docker-compose up" in /Users/dittrich/git/packet_cafe
                Creating network "packet_cafe_default" with the default driver
                Creating network "frontend" with the default driver
                Creating network "results" with the default driver
                Creating network "admin" with the default driver
                Creating network "backend" with the default driver
                Creating network "analysis" with the default driver
                Creating network "preprocessing" with the default driver
                Creating packet_cafe_pcap_stats_1    ... done
                Creating packet_cafe_workers_1       ... done
                Creating packet_cafe_ncapture_1      ... done
                Creating packet_cafe_networkml_1     ... done
                Creating packet_cafe_lb_1            ... done
                Creating packet_cafe_web_1           ... done
                Creating packet_cafe_messenger_1     ... done
                Creating packet_cafe_admin_1         ... done
                Creating packet_cafe_ui_1            ... done
                Creating packet_cafe_pcap-splitter_1 ... done
                Creating packet_cafe_pcap-dot1q_1    ... done
                Creating packet_cafe_pcapplot_1      ... done
                Creating packet_cafe_snort_1         ... done
                Creating packet_cafe_mercury_1       ... done
                Creating packet_cafe_redis_1         ... done

            ..

            With either ``-q`` or normal verbosity, the containers will be run in
            deamon mode (i.e., run in the background) and the command will immediately
            return.

            Adding ``-v`` or ``--debug`` will run the containers in the foreground and
            produce log output from all of the containers, which assists in debugging
            and development testing.

            """)  # noqa
        # TODO(dittrich): Add a debugging section to docs and reference here.
        return add_docker_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] bring up Packet Café Docker stack')
        if containers_are_running():
            if bool(self.app_args.verbose_level):
                logger.info(RUNNING_MSG)
            sys.exit(1)
        repo_dir = parsed_args.packet_cafe_repo_dir
        # TODO(dittrich): Fix this
        remote = "origin"
        branch = parsed_args.packet_cafe_repo_branch
        ensure_clone(url=parsed_args.packet_cafe_github_url,
                     repo_dir=repo_dir,
                     branch=parsed_args.packet_cafe_repo_branch)
        if update_available(repo_dir, remote=remote, branch=branch):
            if parsed_args.update:
                pull(repo_dir, remote=remote, branch=branch)
            else:
                raise RuntimeError(
                    f'[-] An update is available from remote "{remote}"\n'
                    '[-] Use ``-update`` to pull before building')
        elif parsed_args.update:
            logger.info('[-] No updates available')
        if self.app_args.verbose_level > 0:
            logger.info(f'[+] Running "docker-compose up" in {repo_dir}')
        cmd = [
            'docker-compose',
            'up'
        ]
        if self.app_args.verbose_level <= 1:
            cmd.append('-d')
        cmd.append('--no-build')
        # Ensure VOL_PREFIX environment variable is set
        os.environ['VOL_PREFIX'] = self.app_args.packet_cafe_data_dir
        env = get_environment(parsed_args)
        #
        # ERROR: for messenger  Get https://registry-1.docker.io/v2/davedittrich/packet_cafe_messenger/manifests/sha256:...: proxyconnect tcp: dial tcp 192.168.65.1:3129: i/o timeout  # noqa
        #
        env['COMPOSE_HTTP_TIMEOUT'] = '200'
        result = execute(
            cmd=cmd,
            cwd=repo_dir,
            env=env
        )
        if result != 0:
            raise RuntimeError(
                '[-] docker-compose failed to bring containers up'
            )


# vim: set ts=4 sw=4 tw=0 et :
