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

            .. code-block:: console

                $ lim cafe endpoints
                +---------------------------------------------------------------------+
                | Endpoint                                                            |
                +---------------------------------------------------------------------+
                | /api/v1                                                             |
                | /api/v1/id/{session_id}/{req_id}/{tool}/{pcap}/{counter}/{filename} |
                | /api/v1/ids/{session_id}                                            |
                | /api/v1/info                                                        |
                | /api/v1/raw/{tool}/{counter}/{session_id}/{req_id}                  |
                | /api/v1/results/{tool}/{counter}/{session_id}/{req_id}              |
                | /api/v1/status/{session_id}/{req_id}                                |
                | /api/v1/stop/{session_id}/{req_id}                                  |
                | /api/v1/tools                                                       |
                | /api/v1/upload                                                      |
                +---------------------------------------------------------------------+

            ..

            See https://cyberreboot.gitbook.io/packet-cafe/design/api#api-v1
            """)  # noqa
        return add_packet_cafe_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] listing endpoints (api)')
        columns = ['Endpoint']
        response = requests.request("GET", CAFE_API_URL)
        data = [[row] for row in json.loads(response.text)]
        return (columns, data)


# vim: set ts=4 sw=4 tw=0 et :
