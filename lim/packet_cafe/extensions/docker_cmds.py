# -*- coding: utf-8 -*-

import argparse
import git
import logging
import os
import re
import sys
import textwrap

from cliff.command import Command
from cliff.lister import Lister
from lim import execute
from lim.packet_cafe import add_docker_global_options
from lim.packet_cafe import add_packet_cafe_global_options
from lim.packet_cafe import containers_are_running
from lim.packet_cafe import ensure_clone
from lim.packet_cafe import get_containers
from lim.packet_cafe import get_images
from lim.packet_cafe import get_workers_definitions
from lim.packet_cafe import needs_update
from lim.packet_cafe import require_files
from lim.packet_cafe import rm_images


logger = logging.getLogger(__name__)

CONTAINERS_RUNNING_MSG = '[-] packet-cafe containers are already running'
CONTAINERS_NOT_RUNNING_MSG = '[-] packet-cafe containers are not running'
HINT_USE_UPDATE_MSG = "[!] hint: to pull changes, use the '--update' option"
UPDATE_DID_NOTHING_MSG = "[-] '--update' did not have to do anything"
HINT_START_UI_MSG = "[!] hint: use 'lim cafe ui' to start the UI"
HINT_UP_MSG = "[!] hint: use 'lim cafe docker up' to restart the stack"
MIN_IMAGE_COLUMNS = ('ID', 'Repository', 'Tag')

ON_BRANCH_REGEX = re.compile(r'On branch (\w+) ')
HEAD_POSITION_REGEX = re.compile(
    r"Your branch is (.*) [\w/]+ by (\d+) commit")


def print_output(results=[]):
    for line in results:
        sys.stdout.write(line)
        if '\x1b' not in line:
            sys.stdout.write('\n')


def get_environment(args):
    env = dict(os.environ.copy())
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


class ImagesBuild(Command):
    """Build Packet Café Docker images."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        update = parser.add_mutually_exclusive_group(required=False)
        update.add_argument(
            '-u', '--update',
            action='store_true',
            dest='update',
            default=False,
            help=('Update the repository contents before rebuilding '
                  '(default: False)')
        )
        update.add_argument(
            '--ignore-dirty',
            action='store_true',
            dest='ignore_dirty',
            default=False,
            help=('Ignore a dirty repository (default: False)')
        )
        # Text here also copied to docs/packet_cafe.rst
        parser.epilog = textwrap.dedent("""
            Build images from source locally rather than pulling them from Docker Hub.
            This is used for local deployment or development and testing locally. If
            you wish to use images from Docker Hub, use ``lim cafe docker pull``
            instead.

            You will be notified if the GitHub repo has newer content and the program
            will exit. Use the ``--update`` flag to update the repo before building.
            """)  # noqa
        return add_docker_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] locally build Packet Café Docker images')
        if containers_are_running():
            if bool(self.app_args.verbose_level):
                logger.info(CONTAINERS_RUNNING_MSG)
            sys.exit(1)
        repo_dir = parsed_args.packet_cafe_repo_dir
        remote = parsed_args.packet_cafe_repo_remote
        branch = parsed_args.packet_cafe_repo_branch
        repo = ensure_clone(url=parsed_args.packet_cafe_github_url,
                            repo_dir=repo_dir,
                            remote=remote,
                            branch=branch)
        if needs_update(repo, ignore_dirty=parsed_args.ignore_dirty):
            if parsed_args.update:
                repo.remotes.origin.pull()
            else:
                if parsed_args.ignore_dirty:
                    logger.info(HINT_USE_UPDATE_MSG)
                else:
                    raise RuntimeError(HINT_USE_UPDATE_MSG)
        elif parsed_args.update:
            logger.info(UPDATE_DID_NOTHING_MSG)
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
        if self.app_args.verbose_level <= 1 and not self.app_args.debug:
            cmd.append('-d')
        cmd.append('--build')
        if self.app_args.verbose_level > 0:
            logger.info(
                f"[+] running '{' '.join(cmd)}' in {repo_dir}")
        result = execute(cmd=cmd, cwd=repo_dir, env=env)
        if result != 0:
            raise RuntimeError('[-] docker-compose build failed')
        else:
            logger.info(HINT_START_UI_MSG)


class ContainersDown(Command):
    """Bring down Packet Café Docker containers."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        # Text here also copied to docs/packet_cafe.rst
        parser.epilog = textwrap.dedent("""
            Bring down the container stack associated with Packet Café services.

            .. code-block:: none

                $ lim cafe docker down
                [+] running 'docker-compose down' in /Users/dittrich/packet_cafe
                Stopping packet_cafe_redis_1     ... done
                Stopping packet_cafe_web_1       ... done
                Stopping packet_cafe_workers_1   ... done
                Stopping packet_cafe_ui_1        ... done
                Stopping packet_cafe_admin_1     ... done
                Stopping packet_cafe_messenger_1 ... done
                Stopping packet_cafe_lb_1        ... done
                Removing packet_cafe_redis_1         ... done
                Removing packet_cafe_web_1           ... done
                Removing packet_cafe_workers_1       ... done
                Removing packet_cafe_mercury_1       ... done
                Removing packet_cafe_ui_1            ... done
                Removing packet_cafe_pcap-dot1q_1    ... done
                Removing packet_cafe_admin_1         ... done
                Removing packet_cafe_messenger_1     ... done
                Removing packet_cafe_pcap-splitter_1 ... done
                Removing packet_cafe_ncapture_1      ... done
                Removing packet_cafe_pcapplot_1      ... done
                Removing packet_cafe_lb_1            ... done
                Removing packet_cafe_networkml_1     ... done
                Removing packet_cafe_pcap-stats_1    ... done
                Removing packet_cafe_snort_1         ... done
                Removing network packet_cafe_default
                Removing network admin
                Removing network frontend
                Removing network results
                Removing network backend
                Removing network analysis
                Removing network preprocessing
                [+] you can use 'lim cafe docker up' to restart the stack

            After bringing the containers down, you can generally bring them
            back up without having to rebuild them.

            Be aware that when you are doing development on a fork of
            Packet Café, you will need to rebuild the images when you make
            any changes that will affect things inside of running containers.

            If you are just standing things up for the first time, are
            doing local development editing files in your clone, or are
            updating the repository with ``--update``, you will need to
            rebuild the images.
            """)  # noqa
        return add_docker_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] bring down Packet Café Docker stack')
        if not containers_are_running():
            if bool(self.app_args.verbose_level):
                logger.info(CONTAINERS_NOT_RUNNING_MSG)
            sys.exit(1)
        repo_dir = parsed_args.packet_cafe_repo_dir
        try:
            repo = git.Repo(repo_dir)
        except git.exc.NoSuchPathError:
            sys.exit(f"[-] Directory '{repo_dir}' does not exist")
        except git.exc.InvalidGitRepositoryError:
            sys.exit(f"[-] Directory '{repo_dir}' does not "
                     "look like a Git clone")
        cmd = ['docker-compose']
        if self.app_args.verbose_level > 1:
            cmd.append('--verbose')
        cmd.append('down')
        if self.app_args.verbose_level > 0:
            logger.info(f"[+] running '{' '.join(cmd)}' in {repo.working_dir}")
        env = get_environment(parsed_args)
        result = execute(cmd=cmd, cwd=repo.working_dir, env=env)
        if result != 0:
            raise RuntimeError('[-] docker-compose down failed')
        else:
            logger.info(HINT_UP_MSG)


class ImagesList(Lister):
    """List or delete Packet Café related Docker images."""

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
        # Enable all columns if user requests specific columns that
        # might not be in MIN_IMAGE_COLUMNS with ``-c``.
        parser.add_argument(
            '-a', '--all-columns',
            action='store_true',
            dest='all_columns',
            default=('-c' in sys.argv),
            help='Include all available columns (default: False)'
        )
        # Text here also copied to docs/packet_cafe.rst
        parser.epilog = textwrap.dedent("""
            List the images associated with Packet Café services and workers.

            ::

                [+] listing images for service namespace "iqtlabs", tool namespace "iqtlabs"
                +--------------+-------------------------------+--------+
                | ID           | Repository                    | Tag    |
                +--------------+-------------------------------+--------+
                | 7808ad5f74f5 | iqtlabs/packet_cafe_workers   | latest |
                | 83fdfb8db32d | iqtlabs/packet_cafe_redis     | latest |
                | 93fc21bf376a | iqtlabs/packet_cafe_messenger | latest |
                | 11bb63d0c705 | iqtlabs/packet_cafe_lb        | latest |
                | d9194c6daf5f | iqtlabs/packet_cafe_web       | latest |
                | 9fc447bc9fa4 | iqtlabs/packet_cafe_ui        | latest |
                | 8fe33a5eec27 | iqtlabs/packet_cafe_admin     | latest |
                | 1a5cec5e1dab | iqtlabs/tcprewrite_dot1q      | latest |
                | 39c6e9ac53a9 | iqtlabs/pcap_to_node_pcap     | latest |
                | adcc5b1f4213 | iqtlabs/pcap_stats            | latest |
                | 6732f33c5b25 | iqtlabs/ncapture              | latest |
                | 251346bde2eb | iqtlabs/networkml             | v0.6.1 |
                | 6d2d5d790715 | iqtlabs/mercury               | latest |
                | cedfd83f10dc | iqtlabs/snort                 | latest |
                | b56a25f62851 | iqtlabs/pcapplot              | v0.1.7 |
                +--------------+-------------------------------+--------+


            By default, only three columns are shown. If you wish to see all
            available columns, use the ``-a`` option.

            You can remove all of these images from Docker's image storage
            by using the ``--rm`` option.

            If you are doing development on a fork of Packet Café and have
            pushed images to your own namespace on Docker Hub, use the namespace
            and version selection options or environment variables.
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
        service_namespace = parsed_args.docker_service_namespace \
            if parsed_args.docker_service_namespace is not None else 'iqtlabs'
        tool_namespace = parsed_args.docker_tool_namespace \
            if parsed_args.docker_tool_namespace is not None else 'iqtlabs'
        workers_definitions = get_workers_definitions(
            parsed_args.packet_cafe_repo_dir)
        images = get_images(service_namespace=service_namespace,
                            tool_namespace=tool_namespace,
                            workers_definitions=workers_definitions)
        image_set = (
            f'service namespace "{service_namespace}", '
            f'tool namespace "{tool_namespace}"'
        )
        if not len(images):
            raise RuntimeError(f'[-] no images found for {image_set}')
        if self.app_args.verbose_level > 0:
            action = 'removing' if parsed_args.rm_images else 'listing'
            logger.info(f'[+] {action} images for {image_set}')
        columns = MIN_IMAGE_COLUMNS
        if parsed_args.rm_images:
            data = (
                tuple(i[c] for c in columns)
                for i in rm_images(images)
            )
        else:
            if parsed_args.all_columns:
                columns = images[0].keys()
            data = (
                tuple(i[c] for c in columns)
                for i in images
            )
        return columns, data


class ImagesPull(Command):
    """Pull Packet Café Docker images."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        update = parser.add_mutually_exclusive_group(required=False)
        update.add_argument(
            '-u', '--update',
            action='store_true',
            dest='update',
            default=False,
            help=('Update the repository contents before pulling '
                  '(default: False)')
        )
        update.add_argument(
            '--ignore-dirty',
            action='store_true',
            dest='ignore_dirty',
            default=False,
            help=('Ignore a dirty repository (default: False)')
        )
        # Text here also copied to docs/packet_cafe.rst
        parser.epilog = textwrap.dedent("""
            Pull the images associated with Packet Café services and workers from
            Docker Hub to cache them locally.
            """)  # noqa
        return add_docker_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] pull Packet Café Docker images')
        if containers_are_running():
            if bool(self.app_args.verbose_level):
                logger.info(CONTAINERS_RUNNING_MSG)
            sys.exit(1)
        env = get_environment(parsed_args)
        repo_dir = parsed_args.packet_cafe_repo_dir
        repo = ensure_clone(url=parsed_args.packet_cafe_github_url,
                            repo_dir=repo_dir,
                            remote=parsed_args.packet_cafe_repo_remote,
                            branch=parsed_args.packet_cafe_repo_branch)
        if needs_update(repo, ignore_dirty=parsed_args.ignore_dirty):
            if parsed_args.update:
                repo.remotes.origin.pull()
            else:
                if parsed_args.ignore_dirty:
                    logger.info(HINT_USE_UPDATE_MSG)
                else:
                    raise RuntimeError(HINT_USE_UPDATE_MSG)
        # Ensure VOL_PREFIX environment variable is set
        os.environ['VOL_PREFIX'] = self.app_args.packet_cafe_data_dir
        env = get_environment(parsed_args)
        #
        # ERROR: for messenger  Get https://registry-1.docker.io/v2/davedittrich/packet_cafe_messenger/manifests/sha256:...: proxyconnect tcp: dial tcp 192.168.65.1:3129: i/o timeout  # noqa
        #
        env['COMPOSE_HTTP_TIMEOUT'] = '200'
        cmd = ['docker-compose', 'pull']
        if self.app_args.verbose_level > 0:
            logger.info(f"[+] running '{' '.join(cmd)}' in {repo_dir}")
        result = execute(cmd=cmd, cwd=repo_dir, env=env)
        if result != 0:
            raise RuntimeError('[-] failed to pull images')


class ContainersList(Lister):
    """Show running status of Packet Café Docker containers."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        # Text here also copied to docs/packet_cafe.rst
        parser.epilog = textwrap.dedent("""
            Produces a table listing the Docker containers associated with
            Packet Café (by virtue of the ``com.docker.compose.project``
            label being set to ``packet_cafe``).

            ::

                $ lim cafe docker ps
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


            To just get a return value (``0`` for "all running" and ``1`` if not),
            use the ``-q`` option.

            ::

                $ lim -q cafe docker ps
                $ echo $?
                0


            """)  # noqa
        parser = add_packet_cafe_global_options(parser)
        return add_docker_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug(
            '[+] show running status of Packet Café Docker containers')
        service_namespace = parsed_args.docker_service_namespace \
            if parsed_args.docker_service_namespace is not None else 'iqtlabs'
        if not containers_are_running(
            service_namespace=service_namespace
        ):
            if bool(self.app_args.verbose_level):
                logger.info(CONTAINERS_NOT_RUNNING_MSG)
            sys.exit(1)
        elif not bool(self.app_args.verbose_level):
            sys.exit(0)
        # client = docker.from_env()
        # container_ids = [getattr(c, 'id') for c in client.containers.list()]
        columns = ['name', 'short_id', 'image', 'status']
        data = get_containers(columns=columns)
        return columns, data


class ContainersUp(Command):
    """Bring the Packet Café Docker container stack up."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        update = parser.add_mutually_exclusive_group(required=False)
        update.add_argument(
            '-u', '--update',
            action='store_true',
            dest='update',
            default=False,
            help=('Update the repository contents before rebuilding '
                  '(default: False)')
        )
        update.add_argument(
            '--ignore-dirty',
            action='store_true',
            dest='ignore_dirty',
            default=False,
            help=('Ignore a dirty repository (default: False)')
        )
        # Text here also copied to docs/packet_cafe.rst
        parser.epilog = textwrap.dedent("""
            Brings up the container and network stack associated with Packet Café
            services and workers if they are not yet running. Messages from
            ``docker-compose`` will be output to show progress. This can be
            suppressed with the ``-q`` flag.

            Prior to running ``docker-compose``, the repository directory will
            be created (if it does not yet exist) or a ``git fetch`` will be
            attempted to check for updates.

            ::

                $ lim cafe docker up
                [+] branch 'master' is up to date
                [+] running 'docker-compose up -d --no-build' in /Users/dittrich/packet_cafe
                Creating network "packet_cafe_default" with the default driver
                Creating network "admin" with the default driver
                Creating network "frontend" with the default driver
                Creating network "results" with the default driver
                Creating network "backend" with the default driver
                Creating network "analysis" with the default driver
                Creating network "preprocessing" with the default driver
                Creating packet_cafe_admin_1         ... done
                Creating packet_cafe_ncapture_1      ... done
                Creating packet_cafe_networkml_1     ... done
                Creating packet_cafe_pcap-dot1q_1    ... done
                Creating packet_cafe_pcap-splitter_1 ... done
                Creating packet_cafe_snort_1         ... done
                Creating packet_cafe_pcap-stats_1    ... done
                Creating packet_cafe_ui_1            ... done
                Creating packet_cafe_web_1           ... done
                Creating packet_cafe_messenger_1     ... done
                Creating packet_cafe_lb_1            ... done
                Creating packet_cafe_redis_1         ... done
                Creating packet_cafe_mercury_1       ... done
                Creating packet_cafe_workers_1       ... done
                Creating packet_cafe_pcapplot_1      ... done
                [+] you can now use 'lim cafe ui' to start the UI


            With either ``-q`` or normal verbosity, the containers will be run in
            deamon mode (i.e., run in the background) and the command will immediately
            return.

            Adding ``-v`` or ``--debug`` will run the containers in the foreground and
            produce a stream of log output from all of the containers. This assists in
            debugging and development testing. If you interrupt with CTRL-C, the
            containers will be halted and you will need to bring them back up. If
            you bring them down by running ``lim cafe docker down`` in another
            another terminal window, you can observe the shutdown process in the
            log messages and the ``docker-compose`` process will then exit.

            If new updates are available in the remote repository, you will see
            messages about this and ``lim`` will suggest using the ``--update``
            option and exit before starting the containers.  You can skip the
            update and bring the containers up with the ``--ignore-dirty``
            option.

            Note that if you are building images locally, you may not be able
            to use the ``--update`` option with ``up`` due to the state of the
            Git repository. While ``lim`` tries to deal with the situation, it
            can't handle things like merge conflicts. It also depends on what in
            the repo gets changed during the update. In some cases, the local
            images will not need to be rebuilt. In other cases, they will. Docker
            may let you know if a rebuild is necessary.
            """)  # noqa
        # TODO(dittrich): Add a debugging section to docs and reference here.
        return add_docker_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] bring up Packet Café Docker stack')
        if containers_are_running():
            if bool(self.app_args.verbose_level):
                logger.info(CONTAINERS_RUNNING_MSG)
            sys.exit(1)
        repo_dir = parsed_args.packet_cafe_repo_dir
        repo = ensure_clone(url=parsed_args.packet_cafe_github_url,
                            repo_dir=repo_dir,
                            remote=parsed_args.packet_cafe_repo_remote,
                            branch=parsed_args.packet_cafe_repo_branch)
        if needs_update(repo, ignore_dirty=parsed_args.ignore_dirty):
            if parsed_args.update:
                repo.remotes.origin.pull()
            else:
                if parsed_args.ignore_dirty:
                    logger.info(HINT_USE_UPDATE_MSG)
                else:
                    raise RuntimeError(HINT_USE_UPDATE_MSG)
        elif parsed_args.update:
            logger.info(UPDATE_DID_NOTHING_MSG)
        require_files(repo, ['docker-compose.yml'])
        cmd = [
            'docker-compose',
            'up'
        ]
        if self.app_args.verbose_level <= 1 and not self.app_args.debug:
            cmd.append('-d')
        cmd.append('--no-build')
        # Ensure VOL_PREFIX environment variable is set
        os.environ['VOL_PREFIX'] = self.app_args.packet_cafe_data_dir
        env = get_environment(parsed_args)
        #
        # ERROR: for messenger  Get https://registry-1.docker.io/v2/davedittrich/packet_cafe_messenger/manifests/sha256:...: proxyconnect tcp: dial tcp 192.168.65.1:3129: i/o timeout  # noqa
        #
        env['COMPOSE_HTTP_TIMEOUT'] = '200'
        stdout_lines = []
        stderr_lines = []
        if self.app_args.verbose_level > 0:
            logger.info(f"[+] running '{' '.join(cmd)}' in {repo_dir}")
        result = execute(
            cmd=cmd,
            cwd=repo_dir,
            stdout_cb=lambda x: stdout_lines.append(x.decode('utf-8').splitlines()),  # noqa
            stderr_cb=lambda x: stderr_lines.append(x.decode('utf-8').splitlines()),  # noqa
            env=env)
        if result != 0:
            raise RuntimeError(
                '[-] docker-compose failed to bring containers up'
            )
        elif self.app_args.verbose_level <= 1 and not self.app_args.debug:
            logger.info(HINT_START_UI_MSG)


# vim: set ts=4 sw=4 tw=0 et :
