# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap
import sys

from cliff.lister import Lister
from lim.packet_cafe import add_packet_cafe_global_options
from lim.packet_cafe import containers_are_running
from lim.packet_cafe import get_containers

logger = logging.getLogger(__name__)


class Containers(Lister):
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

                $ lim cafe containers
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
        logger.debug('[+] report on Docker containers')
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


# vim: set ts=4 sw=4 tw=0 et :
