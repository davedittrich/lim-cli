# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap

from cliff.lister import Lister
from lim.packet_cafe import add_packet_cafe_global_options
from lim.packet_cafe import get_packet_cafe

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

            .. code-block:: console

                $ lim cafe tools --fit-width
                +---------------+---------------------------+---------+--------+---------------+----------------+----------+---------------+
                | Name          | Image                     | Version | Labels | Stage         | ViewableOutput | Outputs  | Inputs        |
                +---------------+---------------------------+---------+--------+---------------+----------------+----------+---------------+
                | pcapplot      | iqtlabs/pcapplot          | v0.1.5  |        | analysis      | True           | file     | pcap-splitter |
                | pcap-splitter | iqtlabs/pcap-to-node-pcap | v0.11.8 |        | preprocessing | False          | pcap     | pcap-dot1q    |
                | ncapture      | iqtlabs/ncapture          | v0.11.8 |        | preprocessing | False          | pcap     | pcap,pcapng   |
                | pcap-dot1q    | iqtlabs/tcprewrite-dot1q  | v0.11.8 |        | preprocessing | False          | pcap     | ncapture      |
                | networkml     | iqtlabs/networkml         | v0.5.3  |        | analysis      | True           | rabbitmq | pcap-splitter |
                | snort         | iqtlabs/snort             | v0.11.8 |        | analysis      | True           | rabbitmq | pcap,pcapng   |
                | pcap-stats    | iqtlabs/pcap-stats        | v0.11.8 |        | analysis      | True           | rabbitmq | pcap,pcapng   |
                | mercury       | iqtlabs/mercury           | v0.11.8 |        | analysis      | True           | rabbitmq | pcap,pcapng   |
                | p0f           | iqtlabs/p0f               | v0.11.8 |        | analysis      | True           | rabbitmq | pcap-splitter |
                +---------------+---------------------------+---------+--------+---------------+----------------+----------+---------------+

            ..

            See https://iqtlabs.gitbook.io/packet-cafe/design/api#api-v-1-tools
            """)  # noqa
        return add_packet_cafe_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] listing tools')
        packet_cafe = get_packet_cafe(self.app, parsed_args)
        columns = ['Name', 'Image', 'Version', 'Labels',
                   'Stage', 'ViewableOutput', 'Outputs', 'Inputs']
        workers = packet_cafe.get_workers()
        data = []
        for worker in workers:
            data.append(
                ([
                    worker[c[0].lower() + c[1:]]
                    for c in columns
                ]))
        return (columns, data)


# vim: set ts=4 sw=4 tw=0 et :
