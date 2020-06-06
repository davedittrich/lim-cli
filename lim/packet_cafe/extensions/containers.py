# -*- coding: utf-8 -*-

import argparse
import arrow
import docker
import logging
import textwrap

from cliff.lister import Lister
from lim.packet_cafe import add_packet_cafe_global_options
from lim.packet_cafe import get_packet_cafe

logger = logging.getLogger(__name__)


class Containers(Lister):
    """Show status of packet-cafe Docker containers."""

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
        client = docker.from_env()
        container_ids = [getattr(c, 'id') for c in client.containers.list()]
        columns = ['name', 'short_id', 'image', 'status']
        data = []
        for container_id in container_ids:
            container = client.containers.get(container_id)
            data.append([get_text(getattr(container, attr, None))
                         for attr in columns
                         if container.labels.get(
                             'com.docker.compose.project', '') == 'packet_cafe'])
        return columns, data

def get_text(item):
    """Extract desired metadata from Docker container object."""
    if type(item) is str:
        return item
    tags = getattr(item, 'tags', None)
    if tags is not None:
        return tags[0]
    else:
        return str(item)

# vim: set ts=4 sw=4 tw=0 et :
