# -*- coding: utf-8 -*-

# See https://cyberreboot.gitbook.io/packet-cafe/design/api#api-v-1-tools

import json
import requests
import uuid

# TODO(dittrich): https://github.com/Mckinsey666/bullet/issues/2
# Workaround until bullet has Windows missing 'termios' fix.
try:
    from bullet import Bullet
except ModuleNotFoundError:
    pass


CAFE_SERVER = os.getenv('LIM_CAFE_SERVER', '127.0.0.1')
CAFE_UI_PORT = os.getenv('LIM_CAFE_UI_PORT', 80)
CAFE_ADMIN_PORT = os.getenv('LIM_CAFE_ADMIN_PORT', 5001)
CAFE_API_VERSION = 'v1'
CAFE_ADMIN_URL = f'http://{ CAFE_SERVER }:{ CAFE_ADMIN_PORT }/{ CAFE_API_VERSION }'  # noqa
CAFE_API_URL = f'http://{ CAFE_SERVER }:{ CAFE_UI_PORT }/api/{ CAFE_API_VERSION }'  # noqa


def add_packet_cafe_global_options(parser):
    """Add global packet_cafe options."""
    parser.add_argument(
        '--cafe-host',
        action='store',
        type=str,
        metavar='<cafe_host_ip>',
        dest='cafe_host_ip',
        default=CAFE_SERVER,
        help=('IP address for packet_cafe server '
              f'(env var LIM_CAFE_HOST; default: \'{ CAFE_SERVER }\')')
    )
    parser.add_argument(
        '--cafe-ui-port',
        action='store',
        type=int,
        metavar='<cafe_ui_port>',
        dest='cafe_ui_port',
        default=CAFE_UI_PORT,
        help=('TCP port for packet_cafe UI service '
              f'(env var LIM_CAFE_UI_PORT; default: { CAFE_UI_PORT })')
    )
    parser.add_argument(
        '--cafe-admin-port',
        action='store',
        type=int,
        metavar='<cafe_admin_port>',
        dest='cafe_admin_port',
        default=CAFE_ADMIN_PORT,
        help=('TCP port for packet_cafe admin service '
              '(env var LIM_CAFE_ADMIN_PORT; default: { CAFE_ADMIN_PORT })')
    )
    return parser


def _valid_counter(value):
    """Counter must be integer starting with 1."""
    n = int(value)
    if n <= 0:
        raise argparse.ArgumentTypeError(
            f'counter must be positive integer (got { value })')
    return n


def chose_wisely(from_list=[], what='an item', cancel_throws_exception=False):
    choices = ['<CANCEL>'] + from_list
    cli = Bullet(prompt=f'\nChose { what }:',
                 choices=choices,
                 indent=0,
                 align=2,
                 margin=1,
                 shift=0,
                 bullet="→",
                 pad_right=5)
    choice = cli.launch()
    if choice == "<CANCEL>":
        if cancel_throws_exception:
            raise RuntimeError(f'cancelled chosing { what }')
        else:
            return None
    return choice


def get_session_ids():
    """Get IDs from packet-cafe admin service."""
    url = f'{ CAFE_ADMIN_URL }/ids'
    response = requests.request("GET", url)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        return None


def get_requests(sess_id=None):
    """Get requests for a session from packet-cafe admin service."""
    # TODO(dittrich): Mock this for unit testing.
    # if sess_id == "ab7af73526814d58bf35f1399a5594b2":
    #     # return None
    #     return [
    #         {
    #             "id": "ab7af73526814d58bf35f1399a5594b2",
    #             "filename": "trace_ab7af73526814d58bf35f1399a5594b2_2020-04-09_23_38_56.pcap",  # noqa
    #             "tools": ["networkml", "mercury", "pcap-stats", "snort", "p0f", "pcapplot"],   # noqa
    #             "original_filename": "smallFlows.pcap"
    #         }
    #     ]

    url = f'{ CAFE_API_URL }/ids/{ sess_id }'
    response = requests.request("GET", url)
    if response.status_code == 200:
        results = json.loads(response.text)
        return [(i) for i in results]
    else:
        return None


def get_request_ids(sess_id=None):
    """Get IDs from packet-cafe admin service."""
    results = get_requests(sess_id=sess_id)
    if results is not None:
        return [i['id'] for i in results]
    else:
        return None


def get_files():
    """Get all files from packet-cafe admin service."""
    response = requests.request("GET", f'{ CAFE_ADMIN_URL }/id/files')
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        return None


def get_results():
    """Get all results from packet-cafe admin service."""
    response = requests.request("GET", f'{ CAFE_ADMIN_URL }/id/results')
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        return None


def get_tools():
    """Get list of tools that produce output files."""
    workers = get_workers()
    tools = [
        worker['name'] for worker in workers
        if 'file' in worker['outputs']
    ]
    return tools


def get_workers():
    """Get details about workers."""
    response = requests.request("GET", f'{ CAFE_API_URL }/tools')
    if response.status_code == 200:
        return json.loads(response.text)['workers']
    else:
        return None


def get_status(sess_id=None, req_id=None):
    """Get status for session ID + request ID."""
    if sess_id is None:
        raise RuntimeError('sess_id must not be None')
    if req_id is None:
        raise RuntimeError('req_id must not be None')
    url = f'{ CAFE_API_URL }/status/{ sess_id }/{ req_id }'
    response = requests.request("GET", url)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        return None


def get_raw(tool=None, counter=1, sess_id=None, req_id=None):
    """Get raw output from a specific tool, session, and request."""
    if tool is None:
        raise RuntimeError('tool must not be None')
    if sess_id is None:
        raise RuntimeError('sess_id must not be None')
    if req_id is None:
        raise RuntimeError('req_id must not be None')
    url = f'{ CAFE_API_URL }/raw/{ tool }/{ counter }/{ sess_id }/{ req_id }'
    response = requests.request("GET", url)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        return None


def upload(fname=None, sessionId=None):
    """Upload PCAP file to packet-cafe service for processing."""

    # Form data parameters
    # file: object: file to upload
    # sessionId: string: Session ID
    #
    if sessionId is None:
        sessionId = uuid.uuid4()
    with open(fname, 'rb') as f:
        files = {'file': (fname, f.read())}
        data = {'sessionId': sessionId}
        response = requests.post(f'{ CAFE_API_URL }/upload',
                                 files=files,
                                 data=data)
    if response.status_code == 201:
        return json.loads(response.text)
    else:
        return None


__all__ = [
    CAFE_SERVER,
    CAFE_ADMIN_PORT,
    CAFE_UI_PORT,
    CAFE_API_VERSION,
    CAFE_ADMIN_URL,
    CAFE_API_URL,
    add_packet_cafe_global_options,
    chose_wisely,
    get_session_ids,
    get_requests,
    get_request_ids,
    get_files,
    get_results,
    get_tools,
    get_workers,
    get_status,
    get_raw,
    upload,
]


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
