# -*- coding: utf-8 -*-

import argparse
import logging
import os
import sys
import textwrap

from anytree import Node
from anytree import RenderTree
from collections import defaultdict
from cliff.lister import Lister
from lim.packet_cafe import add_packet_cafe_global_options
from lim.packet_cafe import get_packet_cafe

logger = logging.getLogger(__name__)


def match(line=None, contains=[]):
    """
    Return true if line contains all of a set of
    specified strings between '/' characters.
    """
    if line is None:
        raise RuntimeError('[-] no line to search')
    if type(contains) is not list:
        raise RuntimeError('[-] kwarg "contains" must be a list')
    for s in contains:
        if not line.find(f'/{ s }/') >= 0:
            return False
    return True


class Results(Lister):
    """List all files produced by tools."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '--tree',
            action='store_true',
            dest='tree',
            default=False,
            help='Produce tree output rather than table (default: False)'
        )
        parser.add_argument('sess_id', nargs='?', default=None)
        parser.add_argument('req_id', nargs='?', default=None)
        parser.add_argument(
            '-t', '--tool',
            metavar='<tool>',
            dest='tool',
            default=None,
            help='Only show results for specified tool (default: None)'
        )
        parser.epilog = textwrap.dedent("""
            List files produced as a result of processing uploaded files.
            This can produce a large amount of output with very long lines, so
            you may want to use the ``--fit-width`` option to break lines to
            fit the screen.

            You can get a tree listing of files, which is much more compact and
            readable, with the ``--tree`` option.

            .. code-block:: console

                $ lim cafe admin results  --tree
                id
                └── 791e1034-fdb9-4fa4-a410-e1dedef7c0b8
                    └── dcfe1b4dd2a04d559f6600902847a11a
                        ├── mercury
                        │   └── metadata.json
                        ├── networkml
                        │   └── metadata.json
                        ├── p0f
                        │   └── metadata.json
                        ├── pcap-stats
                        │   └── metadata.json
                        ├── pcapplot
                        │   ├── metadata.json
                        │   └── trace_dcfe1b4dd2a04d559f6600902847a11a_2020-06-21_21_44_45-client-ip-147-32-84-165-147-32-80-9-147-32-84-165-wsshort-frame-eth-dns-udp-ip-port-53.pcap
                        │       ├── 1
                        │       │   └── map_ASN-trace_dcfe1b4dd2a04d559f6600902847a11a_2020-06-21_21_44_45-client-ip-147-32-84-165-147-32-80-9-147-32-84-165-wsshort-frame-eth-dns-udp-ip-port-53.pcap.png
                        │       ├── 2
                        │       │   └── map_Private_RFC_1918-trace_dcfe1b4dd2a04d559f6600902847a11a_2020-06-21_21_44_45-client-ip-147-32-84-165-147-32-80-9-147-32-84-165-wsshort-frame-eth-dns-udp-ip-port-53.pcap.png
                        │       ├── 3
                        │       │   └── map_Source_Ports-trace_dcfe1b4dd2a04d559f6600902847a11a_2020-06-21_21_44_45-client-ip-147-32-84-165-147-32-80-9-147-32-84-165-wsshort-frame-eth-dns-udp-ip-port-53.pcap.png
                        │       └── 4
                        │           └── map_Destination_Ports-trace_dcfe1b4dd2a04d559f6600902847a11a_2020-06-21_21_44_45-client-ip-147-32-84-165-147-32-80-9-147-32-84-165-wsshort-frame-eth-dns-udp-ip-port-53.pcap.png
                        └── snort
                            └── metadata.json

            ..

            You can filter results by session, by request, or by tool.
            Filtering matches lines that contain all of the specified values.
            To show results for a specific session or a specific request,
            provide them as arguments to the command.  To show only results
            for a given tool, specify it with the ``-tool`` option.

            .. code-block:: console

                $ lim cafe admin results --tool networkml
                +---------------------------------------------------------------------------------------------------+
                | Results                                                                                           |
                +---------------------------------------------------------------------------------------------------+
                | /id/6f080abf-ef71-461d-b754-a81a54fb5ad5/d709256a73b44f4e82d45f6e4ffd03e5/networkml/metadata.json |
                | /id/86f71039-e6e5-44e2-90b4-3eaf27253d6d/fa142a055de24896923cc69407feeaba/networkml/metadata.json |
                | /id/278adaae-df30-4d7d-883a-990ddcf6ce88/a383d781275f4dbe9e2c78ec4b8abda4/networkml/metadata.json |
                | /id/bd976556-fbc3-4e2e-a808-7024c0c0f69b/6bb276459cba45b3abce9043d0bc0ad9/networkml/metadata.json |
                | /id/bd976556-fbc3-4e2e-a808-7024c0c0f69b/9e74cc6f818c47ea9cd8c8ab94ce93db/networkml/metadata.json |
                +---------------------------------------------------------------------------------------------------+

            ..

            See https://iqtlabs.gitbook.io/packet-cafe/design/api#v-1-id-results
            """)  # noqa
        return add_packet_cafe_global_options(parser)

    # TODO(dittrich): Not DRY. Repeated in lim/packet_cafe/admin/files.py
    def add_node(self, file_path, nodes):
        """Recursively add nodes to branch based on parts of file paths."""
        branch, node = os.path.split(file_path)
        # When the path is down to something like "id", return
        # values will be ('', 'id'). Stop recursion.
        if branch == '':
            return True
        if branch not in nodes:
            self.add_node(branch, nodes)
        nodes[file_path] = Node(node, parent=nodes[branch])

    def take_action(self, parsed_args):
        logger.debug('[+] listing results')
        packet_cafe = get_packet_cafe(self.app, parsed_args)
        results = packet_cafe.get_results()
        if not len(results):
            raise RuntimeError('no results in packet_cafe server')
        if parsed_args.tree:
            root = Node(results[0].split("/")[1])
            nodes = defaultdict()
            nodes[root.name] = root
            for file_path in sorted(results):
                self.add_node(file_path.lstrip('/'), nodes)
            try:
                for pre, _, node in RenderTree(root):
                    print("%s%s" % (pre, node.name))
            except BrokenPipeError:
                # Reopen stdout to avoid recurring exceptions
                sys.stdout = open(os.devnull, 'w')
            return ((), ())
        else:
            columns = ['Results']
            data = []
            # Create a set of filters from args and options.
            contains = [
                item for item
                in [parsed_args.tool, parsed_args.sess_id, parsed_args.req_id]
                if item is not None
            ]
            # Only select items that match all filters
            data = [
                [row] for row in results
                if match(line=row, contains=contains)
             ]
            return (columns, data)


# vim: set ts=4 sw=4 tw=0 et :
