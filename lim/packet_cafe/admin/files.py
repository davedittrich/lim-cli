# -*- coding: utf-8 -*-

import argparse
import logging
import os
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

            See https://cyberreboot.gitbook.io/packet-cafe/design/api#v-1-id-files
            """)  # noqa
        return add_packet_cafe_global_options(parser)

    # TODO(dittrich): Not DRY. Repeated in lim/packet_cafe/admin/results.py
    def add_node(self, parts, nodes):
        """Recursively add nodes to branch based on parts of file paths."""
        branch, node = parts
        branch_parts = os.path.split(branch)
        # When the path is down to something like "/files", return
        # values will be ('/', 'files'). Stop recursion.
        if branch == '/':
            return True
        else:
            branch = branch.lstrip('/')
        if branch_parts[1] not in nodes:
            self.add_node(branch_parts, nodes)
        nodes[node] = Node(node, parent=nodes[branch_parts[1]])

    def take_action(self, parsed_args):
        logger.debug('[+] listing files')
        packet_cafe = get_packet_cafe(self.app, parsed_args)
        files = packet_cafe.get_files()
        if not len(files):
            raise RuntimeError('no files in packet_cafe server')
        if parsed_args.tree:
            root = Node(files[0].split("/")[1])
            nodes = {}
            nodes[root.name] = root
            for file_path in sorted(files):
                parts = os.path.split(file_path)
                self.add_node(parts, nodes)
            for pre, _, node in RenderTree(root):
                try:
                    print("%s%s" % (pre, node.name))
                except BrokenPipeError:
                    pass
            return ((), ())
        else:
            columns = ['File']
            data = [[row] for row in packet_cafe.get_files()]
            return (columns, data)


# vim: set ts=4 sw=4 tw=0 et :
