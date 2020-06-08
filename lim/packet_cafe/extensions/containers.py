# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap

from cliff.lister import Lister
from lim.packet_cafe import add_packet_cafe_global_options
from lim.packet_cafe import containers_are_running
from lim.packet_cafe import get_packet_cafe
from lim.packet_cafe import get_containers

logger = logging.getLogger(__name__)


class Containers(Lister):
    """Show status of Packet Café Docker containers."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.epilog = textwrap.dedent("""
            Produces a table listing the Docker containers associated with
            Packet Café.
            ..
            """)  # noqa
        return add_packet_cafe_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] report on Docker containers')
        if not containers_are_running():
            raise RuntimeError('[-] no packet-cafe containers are running')
        # client = docker.from_env()
        # container_ids = [getattr(c, 'id') for c in client.containers.list()]
        columns = ['name', 'short_id', 'image', 'status']
        data = get_containers(columns=columns)
        return columns, data


# vim: set ts=4 sw=4 tw=0 et :
