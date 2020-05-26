# -*- coding: utf-8 -*-

import argparse
import json
import logging
import textwrap

from cliff.command import Command
from lim.packet_cafe import _valid_counter
from lim.packet_cafe import add_packet_cafe_global_options
from lim.packet_cafe import check_remind_defaulting
from lim.packet_cafe import choose_wisely
from lim.packet_cafe import get_raw
from lim.packet_cafe import get_request_ids
from lim.packet_cafe import get_session_ids
from lim.packet_cafe import get_tools
from lim.packet_cafe import get_last_session_id
from lim.packet_cafe import get_last_request_id
from lim.packet_cafe import report_tree_dict
from lim.packet_cafe import report_tree_json

logger = logging.getLogger(__name__)


def summarize(tool=None, results={}):
    """Summarize output of workers."""
    supported = tool_function.keys()
    if tool not in supported:
        logger.info(f'[-] Reporting for tool "{ tool }" is not yet supported.')
        return []
    return tool_function[tool](results)


def summarize_pcap_stats(results={}):
    """Report on pcap-stats output."""
    report = [
        ""
        "Report for pcap-stats",
        "=====================",
        ""
    ]
    for item in results:
        for key, subresults in item.items():
            report.extend([
                f'{ str(key) }',
                '-' * len(str(key)),
                ""
            ])
            if key in tool_function:
                report.extend(tool_function[key](subresults))
            else:
                report.append(
                    f'[-] Reporting for subtool "pcap-stats:{ key }" '
                    'is not yet supported.'
                )
    return report


def summarize_capinfos(results={}):
    report = []
    for k, v in results.items():
        if type(v) is str:
            report.append(f'{ k }: { v }')
    report.append('')
    return report


def summarize_tshark(results={}):
    report = []
    for k, v in results.items():
        if type(v) is str:
            report.append(f'{ k }: { v }')
        elif type(v) in [list, dict]:
            report.append(f'{ k }: { len(v) }')
        else:
            report.append(f'{ k }: { str(v) }')
    report.append('')
    return report


def summarize_networkml(results={}):
    if not len(results):
        raise RuntimeError('[-] no networkml results to report on')
    report = []
    nodes = dict()
    for item in results:
        report.extend(report_tree_dict(item))
        # for row in results:
        #     for pre, fill, node in report_tree_dict(row):
        #         report.append(f'{ pre }{ node.lines[0] }')
        #         for line in node.lines[1:]:
        #             report.append(f'{ fill }{ line }')
    return report


tool_function = {
    'pcap-stats': summarize_pcap_stats,
    'tshark': summarize_tshark,
    'capinfos': summarize_capinfos,
    'networkml': summarize_networkml,
}


class Report(Command):
    """Produce a report on results of a session+request."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument(
            '-c', '--counter',
            metavar='<counter>',
            type=_valid_counter,
            dest='counter',
            default=1,
            help=('Counter for selecting a specific file '
                  'from a set (default: 1)')
        )
        parser.add_argument(
            '-t', '--tool',
            metavar='<tool>',
            dest='tool',
            default=None,
            help='Only show results for specified tool (default: None)'
        )
        parser.add_argument(
            'sess_id', nargs='?', default=get_last_session_id())
        parser.add_argument(
            'req_id', nargs='?', default=get_last_request_id())
        parser.epilog = textwrap.dedent("""
            Produces a report summarizing the contents of a PCAP file.

            This report is very high level and is intended to illustrate
            how to get situational awareness about flows to guide further
            detailed analysis.
            """)  # noqa
        return add_packet_cafe_global_options(parser)

    def take_action(self, parsed_args):
        logger.debug('[+] report on results from workers')
        ids = get_session_ids()
        if len(ids) == 0:
            raise RuntimeError('[-] no sessions found')
        if parsed_args.sess_id is not None and not parsed_args.choose:
            sess_id = check_remind_defaulting(
                parsed_args.sess_id, 'last session id')
        else:
            sess_id = choose_wisely(
                from_list=ids,
                what="session",
                cancel_throws_exception=True
            )
        if sess_id not in ids:
            raise RuntimeError(f'[-] session ID { sess_id } not found')
        if parsed_args.req_id is not None and not parsed_args.choose:
            req_id = check_remind_defaulting(
                parsed_args.req_id, 'last request id')
        else:
            req_id = choose_wisely(
                from_list=get_request_ids(sess_id=sess_id),
                what="a request",
                cancel_throws_exception=True
            )
        all_tools = get_tools()
        if parsed_args.tool is None:
            tools = all_tools
        else:
            tools = parsed_args.tool.split(',')
        for tool in tools:
            results = get_raw(tool=tool,
                              counter=parsed_args.counter,
                              sess_id=sess_id,
                              req_id=req_id)
            tool_summary = summarize(tool=tool,
                                     results=results)
            print("\n".join(tool_summary))


# vim: set ts=4 sw=4 tw=0 et :
