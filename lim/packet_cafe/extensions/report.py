# -*- coding: utf-8 -*-

import argparse
import arrow
import logging
import textwrap

from cliff.lister import Lister
from collections import OrderedDict
from lim.packet_cafe import add_packet_cafe_global_options
from lim.packet_cafe import get_packet_cafe
from lim.packet_cafe import NO_SESSIONS_MSG

logger = logging.getLogger(__name__)


class Report(Lister):
    """Produce a report on results of a session+request."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '-t', '--tool',
            metavar='<tool>',
            dest='tool',
            default=None,
            help='Only show results for specified tool (default: None)'
        )
        parser.add_argument('sess_id', nargs='?', default=None)
        parser.add_argument('req_id', nargs='?', default=None)
        parser.epilog = textwrap.dedent("""
            Produces a report of the results from one or more workers (tools) to
            summarize the contents of a PCAP file.

            If no tool(s) are specified, reports from all supported tools will
            be produced.

            This report is very high level and is intended to illustrate
            how to get situational awareness about flows in a packet capture
            to guide further more detailed analysis. It may not include all
            details from a given tool. To see the full details from a worker,
            use ``lim cafe raw --tool TOOL`` instead.

            .. code-block:: console

                $ lim cafe report --tool p0f,networkml
                [+] implicitly reusing last session id 46d4f9a9-d5db-487e-a261-91764c044b44
                [+] implicitly reusing last request id a93591b554fe420ebbcf14b67fc8d298

                ************************************************************************************
                                                  Packet Cafe Report

                   Date produced: 2020-06-27T03:54:06.517174+00:00
                   Session ID:    46d4f9a9-d5db-487e-a261-91764c044b44
                   Request ID:    a93591b554fe420ebbcf14b67fc8d298
                   File:          trace_a93591b554fe420ebbcf14b67fc8d298_2020-06-21_21_44_45.pcap
                   Original File: test.pcap

                ************************************************************************************

                Worker results: p0f
                ===================

                +-----------------+----------------+----------+-------------------+---------+-------------------+
                | source_ip       | full_os        | short_os | link              | raw_mtu | mac               |
                +-----------------+----------------+----------+-------------------+---------+-------------------+
                | 10.0.2.102      | Windows 7 or 8 | Windows  | Ethernet or modem | 1500    | 08:00:27:5b:df:e1 |
                | 202.44.54.4     | Windows XP     | Windows  | Ethernet or modem | 1500    | 52:54:00:12:35:02 |
                | 190.110.121.202 | Windows XP     | Windows  | Ethernet or modem | 1500    | 52:54:00:12:35:02 |
                | 112.213.89.90   | Windows XP     | Windows  | Ethernet or modem | 1500    | 52:54:00:12:35:02 |
                +-----------------+----------------+----------+-------------------+---------+-------------------+

                Worker results: networkml
                =========================

                +------------+-------------------+------------+-------------------+----------+-------------+
                | source_ip  | source_mac        | role       |        confidence | behavior | investigate |
                +------------+-------------------+------------+-------------------+----------+-------------+
                | 10.0.2.102 | 08:00:27:5b:df:e1 | GPU laptop | 99.99999999539332 | normal   | no          |
                +------------+-------------------+------------+-------------------+----------+-------------+

            ..
            """)  # noqa
        return add_packet_cafe_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] report on results from workers')
        packet_cafe = get_packet_cafe(self.app, parsed_args)
        ids = packet_cafe.get_session_ids()
        if not len(ids):
            raise RuntimeError(NO_SESSIONS_MSG)
        all_tools = packet_cafe.get_tools()
        if parsed_args.tool is not None:
            for tool in parsed_args.tool.split(','):
                if tool not in all_tools:
                    raise RuntimeError(
                        f"[-] no reportable output for tool '{ tool }'\n"
                        f'[-] use one or more of: { ",".join(all_tools) }')
        sess_id = packet_cafe.get_session_id(
                sess_id=parsed_args.sess_id,
                choose=parsed_args.choose)
        if sess_id not in ids:
            raise RuntimeError(
                f'[-] session ID { sess_id } not found')
        req_id = packet_cafe.get_request_id(
                sess_id=sess_id,
                req_id=parsed_args.req_id,
                choose=parsed_args.choose)
        try:
            request = [r for r in packet_cafe.get_requests(sess_id=sess_id)
                       if r['id'] == req_id][0]
        except IndexError:
            raise RuntimeError('[-] failed to get request details')
        # Save for reporting methods
        self.parsed_args = parsed_args
        if self.app_args.verbose_level >= 1:
            header_decorator = "*" * (len(request['filename']) + 21)
            try:
                print(textwrap.dedent(f"""
                    { header_decorator }
                    { " " * (int(len(header_decorator) / 2) - 8) }Packet Cafe Report

                       Date produced: { arrow.utcnow() }
                       Session ID:    { sess_id }
                       Request ID:    { req_id }
                       File:          { request['filename']}
                       Original File: { request['original_filename']}

                    { header_decorator }
                    """))  # noqa
            except BrokenPipeError:
                pass
        if parsed_args.tool is None:
            # Preserve report ordering. Because, CDO.
            # (It's like OCD, but the letters are in alphabetic order.)
            tools = [k for k in self.tool_function.keys()
                     if k in all_tools]
        else:
            tools = parsed_args.tool.split(',')
        for tool in tools:
            results = packet_cafe.get_raw(tool=tool,
                                          sess_id=sess_id,
                                          req_id=req_id)
            self.summarize(tool=tool,
                           results=results,
                           sess_id=sess_id,
                           req_id=req_id)
        # Return nothing as we have already output report subcomponents
        # directly. Kind of a hack, but what the hack?
        return (), ()

    def summarize(self, tool=None, results={}, sess_id=None, req_id=None):
        """Summarize output of workers."""
        supported = self.tool_function.keys()
        if tool not in supported:
            logger.debug(f'[-] Reporting for tool "{ tool }" '
                         'is not yet supported.')
        else:
            header = textwrap.dedent(f"""
                Worker results: { tool }
                ================{ "=" * len(tool) }
                """)
            logger.info(header)
            self.tool_function[tool](self,
                                     results=results,
                                     sess_id=sess_id,
                                     req_id=req_id)

    def summarize_pcap_stats(self, results={}, sess_id=None, req_id=None):
        """Report on pcap-stats output."""
        for item in results:
            for key, subresults in item.items():
                sub_report_header = textwrap.dedent(f"""\
                    { str(key) }
                    {'-' * len(str(key)) }
                """)
                if key in self.tool_function:
                    logger.info(sub_report_header)
                    self.tool_function[key](self,
                                            results=subresults,
                                            sess_id=sess_id,
                                            req_id=req_id)
                else:
                    logger.info(
                        f'[-] Reporting for subtool "pcap-stats:{ key }" '
                        'is not yet supported.'
                    )

    def summarize_capinfos(self, results={}, sess_id=None, req_id=None):
        columns = ('Field', 'Value')
        data = []
        for k, v in results.items():
            if type(v) is str:
                data.append((k, v))
        self.produce_output(self.parsed_args, columns, data)

    def summarize_tshark(self, results={}, sess_id=None, req_id=None):
        columns = ('Field', 'Value')
        data = []
        for k, v in results.items():
            if type(v) is str:
                data.append((k, v))
            elif type(v) in [list, dict]:
                data.append((k, len(v)))
            else:
                data.append((k, str(v)))
        self.produce_output(self.parsed_args, columns, data)

    def summarize_networkml(self, results={}, sess_id=None, req_id=None):
        if not len(results):
            raise RuntimeError('[-] no networkml results to report on')
        nodes = dict()
        columns = ['source_ip', 'source_mac', 'role',
                   'confidence', 'behavior', 'investigate']
        data = []
        for item in results:
            for key, result in item.items():
                if key == req_id:
                    node = f"{ result['source_ip'] }-{ result['source_mac'] }"
                    if node not in nodes:
                        data.append((
                            result['source_ip'],
                            result['source_mac'],
                            "\n".join(result['classification']['labels']),
                            "\n".join(['{0:.5f}'.format(i)
                                       for i in result['classification']['confidences']]),  # noqa
                            result['decisions']['behavior'],
                            "yes" if result['decisions']['investigate'] else "no",  # noqa
                        ))
                    nodes[node] = True
        self.produce_output(self.parsed_args, columns, data)

    def summarize_snort(self, results={}, sess_id=None, req_id=None):
        columns = ('Field', 'Value')
        data = []
        for item in results:
            for k, v in item.items():
                if k.endswith(':'):
                    k = k[:-1]
                if type(v) is str:
                    data.append((k, None if v == '' else v))
                elif type(v) in [list, dict]:
                    # Make sure something shows up for no results
                    if not bool(len(v)) or len(v) == 1 and v[0] == '':
                        data.append((k, None))
                    else:
                        data.append((k, "\n".join(v)))
                else:
                    data.append((k, str(v)))
        self.produce_output(self.parsed_args, columns, data)

    def summarize_p0f(self, results={}, sess_id=None, req_id=None):
        if not len(results):
            raise RuntimeError('[-] no p0f results to report on')
        columns = ['source_ip', 'full_os', 'short_os',
                   'link', 'raw_mtu', 'mac']
        data = []
        for item in results:
            for source_ip, result in item.items():
                data.append(
                    [source_ip] + [result[k] if k in result else None
                                   for k in columns[1:]]
                )
        self.produce_output(self.parsed_args, columns, data)

    # Reports in order of detail (highest level detail to
    # lowest level of detail.)
    tool_function = OrderedDict({
        'p0f': summarize_p0f,
        'networkml': summarize_networkml,
        'pcap-stats': summarize_pcap_stats,
        'tshark': summarize_tshark,
        'capinfos': summarize_capinfos,
        'snort': summarize_snort,
    })


# vim: set ts=4 sw=4 tw=0 et :
