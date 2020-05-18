# -*- coding: utf-8 -*-

import argparse
import json
import logging
import requests
import textwrap

from cliff.show import ShowOne
from lim.packet_cafe import CAFE_API_URL
from lim.packet_cafe import add_packet_cafe_global_options

logger = logging.getLogger(__name__)


class ApiInfo(ShowOne):
    """Return basic information about the packet-cafe service."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.epilog = textwrap.dedent("""
            Return basic information about the packet-cafe service.

            .. code-block:: console

                $ lim cafe info
                +----------+---------------------------------+
                | Field    | Value                           |
                +----------+---------------------------------+
                | url      | http://127.0.0.1:80/api/v1/info |
                | version  | v0.1.0                          |
                | hostname | bf1456253115                    |
                +----------+---------------------------------+

            ..

            Note that the last session ID and last request ID are found in the output
            of ``lim cafe admin info`` (not ``lim cafe info``).

            See https://cyberreboot.gitbook.io/packet-cafe/design/api#api-v-1-info
            """)  # noqa
        return add_packet_cafe_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] showing info (api)')
        # Doing this manually here to include URL in output.
        url = f'{ CAFE_API_URL }/info'
        response = requests.request("GET", url)
        columns = ['url']
        data = [(url)]
        for k, v in json.loads(response.text).items():
            columns.append(k)
            data.append((v))
        return (columns, data)


# vim: set ts=4 sw=4 tw=0 et :
