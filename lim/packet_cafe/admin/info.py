# -*- coding: utf-8 -*-

import argparse
import json
import logging
import requests
import textwrap

from cliff.show import ShowOne
from lim.packet_cafe import CAFE_ADMIN_URL
from lim.packet_cafe import add_packet_cafe_global_options
from lim.packet_cafe import get_last_session_id
from lim.packet_cafe import get_last_request_id

logger = logging.getLogger(__name__)


class AdminInfo(ShowOne):
    """Return basic information about the packet-cafe service."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.epilog = textwrap.dedent("""
            Return basic information about the packet-cafe service.

            See https://cyberreboot.gitbook.io/packet-cafe/design/api#v-1-info
            """)
        return add_packet_cafe_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] showing info (admin)')
        # Doing this manually here to include URL in output.
        url = f'{ CAFE_ADMIN_URL }/info'
        response = requests.request("GET", url)
        columns = ['url', 'last_session', 'last_request']
        data = [url, get_last_session_id(), get_last_request_id()]
        for k, v in json.loads(response.text).items():
            columns.append(k)
            data.append((v))
        return (columns, data)


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
