# -*- coding: utf-8 -*-

import argparse
import json
import logging
import requests
import textwrap

from cliff.lister import Lister
from lim.packet_cafe import CAFE_ADMIN_URL

logger = logging.getLogger(__name__)


class Endpoints(Lister):
    """List available packet-cafe admin endpoints."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.epilog = textwrap.dedent("""
            List the available admin endpoints for this packet-cafe server.

            See https://cyberreboot.gitbook.io/packet-cafe/design/api#v1
            """)
        return parser

    def take_action(self, parsed_args):
        logger.debug('[+] listing endpoints (admin)')
        columns = ['Endpoint']
        response = requests.request("GET", CAFE_ADMIN_URL)
        data = [[row] for row in json.loads(response.text)]
        return (columns, data)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
