# -*- coding: utf-8 -*-

import argparse
import json
import logging
import requests
import textwrap

from cliff.lister import Lister
from lim.packet_cafe import CAFE_API_URL

logger = logging.getLogger(__name__)


class Tools(Lister):
    """List tools used by workers in the packet-cafe server."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.epilog = textwrap.dedent("""
            List tools used by workers in the packet-cafe server.

            See https://cyberreboot.gitbook.io/packet-cafe/design/api#api-v-1-tools
            """)  # noqa
        return parser

    def take_action(self, parsed_args):
        logger.debug('[+] listing tools')
        columns = ['Name', 'Image', 'Version', 'Labels',
                   'Stage', 'ViewableOutput', 'Outputs', 'Inputs']
        response = requests.request("GET", f'{CAFE_API_URL}/tools')
        workers = json.loads(response.text)['workers']
        data = list()
        for tool in workers:
            data.append(
                ([
                    tool[c[0].lower() + c[1:]]
                    for c in columns
                ]))
        return (columns, data)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
