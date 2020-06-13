# -*- coding: utf-8 -*-

import argparse
import logging
import textwrap

from cliff.show import ShowOne
from lim.packet_cafe import add_packet_cafe_global_options
from lim.packet_cafe import get_packet_cafe

logger = logging.getLogger(__name__)


class AdminInfo(ShowOne):
    """Return basic information about the packet-cafe service."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.epilog = textwrap.dedent("""
            Return basic information about the packet-cafe service.

            Use this command to determine the last session ID and last
            request ID, if available.

            .. code-block:: console

                $ lim cafe admin info
                +--------------+--------------------------------------+
                | Field        | Value                                |
                +--------------+--------------------------------------+
                | url          | http://127.0.0.1:5001/v1/info        |
                | last_session | 9a949fe6-6520-437f-89ec-e7af6925b1e0 |
                | last_request | 81778bb8a9b946ba82659732baacdb44     |
                | version      | v0.1.0                               |
                | hostname     | 5df1f9a14bff                         |
                +--------------+--------------------------------------+

            ..

            To programmatically obtain the last session ID for use in other
            scripts, do the following:

            .. code-block:: console

                $ lim cafe admin info -f shell
                url="http://127.0.0.1:5001/v1/info"
                last_session="9a949fe6-6520-437f-89ec-e7af6925b1e0"
                last_request="81778bb8a9b946ba82659732baacdb44"
                version="v0.1.0"
                hostname="5df1f9a14bff"

            ..

            See https://cyberreboot.gitbook.io/packet-cafe/design/api#v-1-info
            """)
        return add_packet_cafe_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] showing info (admin)')
        packet_cafe = get_packet_cafe(self.app, parsed_args)
        response = packet_cafe.get_admin_info()
        columns = ['url', 'last_session', 'last_request']
        data = [
            packet_cafe.get_admin_url(),
            packet_cafe.get_last_session_id(),
            packet_cafe.get_last_request_id()
        ]
        for k, v in response.items():
            columns.append(k)
            data.append((v))
        return (columns, data)


# vim: set ts=4 sw=4 tw=0 et :
