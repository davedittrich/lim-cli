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


class Files(Lister):
    """List files in packet-cafe server."""

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
        parser.epilog = textwrap.dedent("""
            Lists all files uploaded into the packet-cafe server.  This can produce
            a large amount of output with very long lines, so you may want to use the
            ``--fit-width`` option to break lines to fit the screen.

            You can get a tree listing of files, which is much more compact and
            readable, with the ``--tree`` option.


            .. code-block:: console

                $ lim cafe admin files  --tree
                files
                └── 791e1034-fdb9-4fa4-a410-e1dedef7c0b8
                    └── dcfe1b4dd2a04d559f6600902847a11a
                        ├── tcprewrite-dot1q-2020-06-21-21_44_49.215175-UTC
                        │   ├── pcap-node-splitter-2020-06-21-21_44_53.389934-UTC
                        │   │   ├── clients
                        │   │   │   ├── combined.csv.gz
                        │   │   │   ├── trace_dcfe1b4dd2a04d559f6600902847a11a_2020-06-21_21_44_45-client-ip-147-32-84-165-147-32-80-9-147-32-84-165-wsshort-frame-eth-dns-udp-ip-port-53.pcap
                        │   │   │   ├── trace_dcfe1b4dd2a04d559f6600902847a11a_2020-06-21_21_44_45-client-ip-147-32-84-165-147-32-80-9-147-32-84-165-wsshort-frame-eth-dns-udp-ip-port-53.pcap.csv.gz
                        │   │   │   ├── trace_dcfe1b4dd2a04d559f6600902847a11a_2020-06-21_21_44_45-client-ip-147-32-84-79-147-32-84-165-147-32-84-79-data-udp-frame-eth-ip-port-0.pcap
                        │   │   │   └── trace_dcfe1b4dd2a04d559f6600902847a11a_2020-06-21_21_44_45-client-ip-147-32-84-79-147-32-84-165-147-32-84-79-data-udp-frame-eth-ip-port-0.pcap.csv.gz
                        │   │   └── servers
                        │   │       ├── trace_dcfe1b4dd2a04d559f6600902847a11a_2020-06-21_21_44_45-server-ip-118-228-148-32-118-228-148-32-147-32-84-165-2-4-5-4-1-1-4-2-tcp-frame-eth-ip-port-80.pcap
                        │   │       ├── trace_dcfe1b4dd2a04d559f6600902847a11a_2020-06-21_21_44_45-server-ip-123-126-51-33-123-126-51-33-147-32-84-165-wsshort-eth-tcp-http-frame-ip-port-80.pcap
                        │   │       ├── trace_dcfe1b4dd2a04d559f6600902847a11a_2020-06-21_21_44_45-server-ip-123-126-51-57-123-126-51-57-147-32-84-165-wsshort-eth-tcp-http-frame-ip-port-80.pcap
                        │   │       ├── trace_dcfe1b4dd2a04d559f6600902847a11a_2020-06-21_21_44_45-server-ip-123-126-51-64-123-126-51-64-147-32-84-165-wsshort-eth-tcp-http-frame-ip-port-80.pcap
                        │   │       ├── trace_dcfe1b4dd2a04d559f6600902847a11a_2020-06-21_21_44_45-server-ip-123-126-51-65-123-126-51-65-147-32-84-165-wsshort-eth-tcp-http-frame-ip-port-80.pcap
                        │   │       ├── trace_dcfe1b4dd2a04d559f6600902847a11a_2020-06-21_21_44_45-server-ip-147-32-80-9-147-32-80-9-147-32-84-165-wsshort-frame-eth-dns-udp-ip-port-53.pcap
                        │   │       ├── trace_dcfe1b4dd2a04d559f6600902847a11a_2020-06-21_21_44_45-server-ip-147-32-84-165-147-32-84-165-147-32-84-79-data-udp-frame-eth-ip-port-0.pcap
                        │   │       ├── trace_dcfe1b4dd2a04d559f6600902847a11a_2020-06-21_21_44_45-server-ip-147-32-84-255-147-32-84-165-147-32-84-255-nbns-frame-eth-wsshort-udp-ip-port-137.pcap
                        │   │       ├── trace_dcfe1b4dd2a04d559f6600902847a11a_2020-06-21_21_44_45-server-ip-147-32-84-79-147-32-84-165-147-32-84-79-icmp-wsshort-frame-eth-ip.pcap
                        │   │       ├── trace_dcfe1b4dd2a04d559f6600902847a11a_2020-06-21_21_44_45-server-ip-195-113-232-73-147-32-84-165-195-113-232-73-wsshort-eth-tcp-http-frame-ip-port-80.pcap
                        │   │       ├── trace_dcfe1b4dd2a04d559f6600902847a11a_2020-06-21_21_44_45-server-ip-209-85-149-160-147-32-84-165-209-85-149-160-wsshort-eth-tcp-http-frame-ip-port-80.pcap
                        │   │       ├── trace_dcfe1b4dd2a04d559f6600902847a11a_2020-06-21_21_44_45-server-ip-218-29-42-137-147-32-84-165-218-29-42-137-wsshort-eth-tcp-http-frame-ip-port-80.pcap
                        │   │       ├── trace_dcfe1b4dd2a04d559f6600902847a11a_2020-06-21_21_44_45-server-ip-220-181-111-147-147-32-84-165-220-181-111-147-wsshort-eth-tcp-http-frame-ip-port-80.pcap
                        │   │       ├── trace_dcfe1b4dd2a04d559f6600902847a11a_2020-06-21_21_44_45-server-ip-220-181-69-213-147-32-84-165-2-4-5-4-1-1-4-2-220-181-69-213-tcp-frame-eth-ip-port-80.pcap
                        │   │       ├── trace_dcfe1b4dd2a04d559f6600902847a11a_2020-06-21_21_44_45-server-ip-61-135-188-157-147-32-84-165-2-4-5-4-1-1-4-2-61-135-188-157-tcp-frame-eth-ip-port-80.pcap
                        │   │       ├── trace_dcfe1b4dd2a04d559f6600902847a11a_2020-06-21_21_44_45-server-ip-61-135-188-210-147-32-84-165-61-135-188-210-wsshort-eth-tcp-http-frame-ip-port-80.pcap
                        │   │       ├── trace_dcfe1b4dd2a04d559f6600902847a11a_2020-06-21_21_44_45-server-ip-61-135-188-212-147-32-84-165-61-135-188-212-wsshort-eth-tcp-http-frame-ip-port-80.pcap
                        │   │       └── trace_dcfe1b4dd2a04d559f6600902847a11a_2020-06-21_21_44_45-server-ip-61-135-189-50-147-32-84-165-2-4-5-4-1-1-4-2-61-135-189-50-tcp-frame-eth-ip-port-80.pcap
                        │   └── trace_dcfe1b4dd2a04d559f6600902847a11a_2020-06-21_21_44_45.pcap
                        ├── test.pcap
                        └── trace_dcfe1b4dd2a04d559f6600902847a11a_2020-06-21_21_44_45.pcap

            ..

            See https://iqtlabs.gitbook.io/packet-cafe/design/api#v-1-id-files
            """)  # noqa
        return add_packet_cafe_global_options(parser)

    # TODO(dittrich): Not DRY. Repeated in lim/packet_cafe/admin/results.py
    def add_node(self, file_path, nodes):
        """Recursively add nodes to branch based on parts of file paths."""
        branch, node = os.path.split(file_path)
        # When the path is down to something like "files", return
        # values will be ('', 'files'). Stop recursion.
        if branch == '':
            return True
        if branch not in nodes:
            self.add_node(branch, nodes)
        nodes[file_path] = Node(node, parent=nodes[branch])

    def take_action(self, parsed_args):
        logger.debug('[+] listing files')
        packet_cafe = get_packet_cafe(self.app, parsed_args)
        files = packet_cafe.get_files()
        if not len(files):
            raise RuntimeError('no files in packet_cafe server')
        if parsed_args.tree:
            root = Node(files[0].split("/")[1])
            nodes = defaultdict()
            nodes[root.name] = root
            for file_path in sorted(files):
                self.add_node(file_path.lstrip('/'), nodes)
            try:
                for pre, _, node in RenderTree(root):
                    print("%s%s" % (pre, node.name))
            except BrokenPipeError:
                # Reopen stdout to avoid recurring exceptions
                sys.stdout = open(os.devnull, 'w')
            return ((), ())
        else:
            columns = ['File']
            data = [[row] for row in packet_cafe.get_files()]
            return (columns, data)


# vim: set ts=4 sw=4 tw=0 et :
