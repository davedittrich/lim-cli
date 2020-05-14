# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap

from cliff.lister import Lister
from lim.packet_cafe import add_packet_cafe_global_options
from lim.packet_cafe import get_workers

logger = logging.getLogger(__name__)


class Tools(Lister):
    """
    List details about workers in the packet-cafe server.

    The API endpoint should be called "workers" if you ask me, since the
    "tool" is just part of the details returned."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.epilog = textwrap.dedent("""
            List tools used by workers in the packet-cafe server.

            See https://cyberreboot.gitbook.io/packet-cafe/design/api#api-v-1-tools
            """)  # noqa
        return add_packet_cafe_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] listing tools')
        columns = ['Name', 'Image', 'Version', 'Labels',
                   'Stage', 'ViewableOutput', 'Outputs', 'Inputs']
        workers = get_workers()
        data = list()
        for worker in workers:
            data.append(
                ([
                    worker[c[0].lower() + c[1:]]
                    for c in columns
                ]))
        return (columns, data)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
