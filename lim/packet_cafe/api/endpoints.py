# -*- coding: utf-8 -*-

import argparse
import json
import logging
import requests
import textwrap

from cliff.lister import Lister
from lim.packet_cafe import CAFE_API_URL
from lim.packet_cafe import add_packet_cafe_global_options

logger = logging.getLogger(__name__)


class Endpoints(Lister):
    """List available packet-cafe API endpoints."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.epilog = textwrap.dedent("""
            List the available API endpoints for this packet-cafe server.

            See https://cyberreboot.gitbook.io/packet-cafe/design/api#api-v1
            """)
        return add_packet_cafe_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] listing endpoints (api)')
        columns = ['Endpoint']
        response = requests.request("GET", CAFE_API_URL)
        data = [[row] for row in json.loads(response.text)]
        return (columns, data)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
