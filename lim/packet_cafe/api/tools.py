# -*- coding: utf-8 -*-

import argparse
import logging
import os
import textwrap

from cliff.lister import Lister
from lim.packet_cafe import add_docker_global_options
from lim.packet_cafe import add_packet_cafe_global_options
from lim.packet_cafe import get_branch
from lim.packet_cafe import get_packet_cafe
from lim.packet_cafe import get_workers_definitions

logger = logging.getLogger(__name__)


class Tools(Lister):
    """
    List details about workers in the packet-cafe server.

    The API endpoint should be called "workers" if you ask me, since the
    "tool" is just part of the details returned."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '--definitions',
            action='store_true',
            dest='definitions',
            default=False,
            help=('Show definitions from JSON files, not live '
                  '(default: False)')
        )

        parser.epilog = textwrap.dedent("""
            List tools used by workers in the packet-cafe server.

            .. code-block:: console

                $ lim cafe tools --fit-width
                +---------------+---------------------------+---------+--------+---------------+----------------+----------+---------------+
                | Name          | Image                     | Version | Labels | Stage         | ViewableOutput | Outputs  | Inputs        |
                +---------------+---------------------------+---------+--------+---------------+----------------+----------+---------------+
                | pcapplot      | iqtlabs/pcapplot          | v0.1.5  |        | analysis      | True           | file     | pcap-splitter |
                | pcap-splitter | iqtlabs/pcap_to_node_pcap | v0.11.8 |        | preprocessing | False          | pcap     | pcap-dot1q    |
                | ncapture      | iqtlabs/ncapture          | v0.11.8 |        | preprocessing | False          | pcap     | pcap,pcapng   |
                | pcap-dot1q    | iqtlabs/tcprewrite_dot1q  | v0.11.8 |        | preprocessing | False          | pcap     | ncapture      |
                | networkml     | iqtlabs/networkml         | v0.5.3  |        | analysis      | True           | rabbitmq | pcap-splitter |
                | snort         | iqtlabs/snort             | v0.11.8 |        | analysis      | True           | rabbitmq | pcap,pcapng   |
                | pcap_stats    | iqtlabs/pcap_stats        | v0.11.8 |        | analysis      | True           | rabbitmq | pcap,pcapng   |
                | mercury       | iqtlabs/mercury           | v0.11.8 |        | analysis      | True           | rabbitmq | pcap,pcapng   |
                | p0f           | iqtlabs/p0f               | v0.11.8 |        | analysis      | True           | rabbitmq | pcap-splitter |
                +---------------+---------------------------+---------+--------+---------------+----------------+----------+---------------+

            ..

            The ``--definitions`` option will show the definitions as found in the
            ``workers.d`` drop-in directory within the repository directory, rather
            than from the running system via the API. The ``--packet-cafe-repo-dir``
            option controls which directory is used. This option is most useful
            when developing and testing your own images to verify what images
            will be used by workers after bringing up the stack.

            .. code-block:: console

                $ lim cafe tools --definitions
                [+] definitions '/Users/dittrich/packet_cafe/workers/workers.d' (branch 'master')
                . . .

            ..

            See https://iqtlabs.gitbook.io/packet-cafe/design/api#api-v-1-tools
            """)  # noqa
        parser = add_docker_global_options(parser)
        return add_packet_cafe_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] listing tools')
        packet_cafe = get_packet_cafe(self.app, parsed_args)
        columns = ['Name', 'Image', 'Version', 'Labels',
                   'Stage', 'ViewableOutput', 'Outputs', 'Inputs']
        repo_dir = parsed_args.packet_cafe_repo_dir
        branch = get_branch(repo_dir)
        if parsed_args.definitions:
            logger.info(
                "[+] definitions from "
                f"{os.path.join(repo_dir, 'workers', 'workers.d')} "
                f"(branch '{branch}')")
            workers_definitions = get_workers_definitions(
                repo_dir=repo_dir,
                flatten=True)
            workers = workers_definitions['workers']
        else:
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
