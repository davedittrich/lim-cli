# -*- coding: utf-8 -*-

import argparse
import logging
import os
import textwrap
import sys

from cliff.command import Command
from cliff.lister import Lister
from lim.packet_cafe import add_docker_global_options
from lim.packet_cafe import add_packet_cafe_global_options
from lim.packet_cafe import containers_are_running
from lim.packet_cafe import get_containers
from lim.packet_cafe import get_images
from lim.packet_cafe import get_output_realtime


logger = logging.getLogger(__name__)


def print_output(results=[]):
    for line in results:
        sys.stdout.write(line)
        if '\x1b' not in line:
            sys.stdout.write('\n')


def get_environment(args):
    env = os.environ.copy()
    env["SERVICE_NAMESPACE"] = args.docker_service_namespace
    env["SERVICE_VERSION"] = args.docker_service_version
    env["TOOL_NAMESPACE"] = args.docker_tool_namespace
    env["REPO_DIR"] = args.packet_cafe_repo_dir
    env["GITHUB_URL"] = args.packet_cafe_github_url
    return env


class ContainersBuild(Command):
    """Build Packet Café Docker containers."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        # Text here also copied to docs/packet_cafe.rst
        parser.epilog = textwrap.dedent("""
            Pull the containers associated with Packet Café services and workers from
            Docker Hub to cache them locally.
            """)  # noqa
        return add_docker_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] locally build Packet Café Docker containers')
        cmd = ['docker-compose', 'up']
        if self.app_args.verbose_level <= 1:
            cmd.append('-d')
        cmd.append('--build')
        result = get_output_realtime(
            cmd=cmd,
            cwd=parsed_args.packet_cafe_repo_dir,
            env=get_environment(parsed_args)
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
        cmd = ['docker-compose']
        if self.app_args.verbose_level > 1:
            cmd.append('--verbose')
        cmd.append('down')
        result = get_output_realtime(
            cmd=cmd,
            cwd=parsed_args.packet_cafe_repo_dir,
            env=get_environment(parsed_args)
        )
        if result != 0:
            raise RuntimeError('[-] docker-compose down failed')


class ContainersImages(Lister):
    """List Packet Café related Docker images."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
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
        images = get_images(filter=[parsed_args.docker_service_namespace,
                                    parsed_args.docker_tool_namespace])
        if not len(images):
            raise RuntimeError('[-] no images found')
        columns = images[0].keys()
        data = ((i.values()) for i in images)
        return columns, data


class ContainersPull(Command):
    """Pull Packet Café Docker containers."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        # Text here also copied to docs/packet_cafe.rst
        parser.epilog = textwrap.dedent("""
            Pull the containers associated with Packet Café services and workers from
            Docker Hub to cache them locally.
            """)  # noqa
        return add_docker_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] pull Packet Café Docker containers')
        env = get_environment(parsed_args)
        #
        # ERROR: for messenger  Get https://registry-1.docker.io/v2/davedittrich/packet_cafe_messenger/manifests/sha256:...: proxyconnect tcp: dial tcp 192.168.65.1:3129: i/o timeout  # noqa
        #
        env['COMPOSE_HTTP_TIMEOUT'] = '200'
        result = get_output_realtime(
            cmd=['docker-compose', 'pull'],
            cwd=parsed_args.packet_cafe_repo_dir,
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
            Produce a table listing the Docker containers associated with
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

                $ lim -q cafe containers
                $ echo $?
                0
            ..
            """)  # noqa
        return add_packet_cafe_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] report on Packet Café Docker containers')
        if not containers_are_running():
            if bool(self.app_args.verbose_level):
                logger.info('[-] no packet-cafe containers are running')
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
        # Text here also copied to docs/packet_cafe.rst
        parser.epilog = textwrap.dedent("""
            Bring up the container and network stack associated with Packet Café
            services and workers.
            """)  # noqa
        return add_docker_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] bring up Packet Café Docker stack')
        if containers_are_running():
            if bool(self.app_args.verbose_level):
                logger.info('[-] packet-cafe containers are already running')
            sys.exit(1)
        cmd = ['docker-compose', 'up']
        if self.app_args.verbose_level <= 1:
            cmd.append('-d')
        cmd.append('--no-build')
        result = get_output_realtime(
            cmd=cmd,
            cwd=parsed_args.packet_cafe_repo_dir,
            env=get_environment(parsed_args)
        )
        if result != 0:
            raise RuntimeError(
                '[-] docker-compose failed to bring containers up'
            )


# vim: set ts=4 sw=4 tw=0 et :
