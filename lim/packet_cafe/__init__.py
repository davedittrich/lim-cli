# -*- coding: utf-8 -*-

# See https://cyberreboot.gitbook.io/packet-cafe/design/api#api-v-1-tools

import argparse
import logging
import json
import os
import requests
import sys
import time
import uuid


from lim.utils import Timer


# TODO(dittrich): https://github.com/Mckinsey666/bullet/issues/2
# Workaround until bullet has Windows missing 'termios' fix.
try:
    from bullet import Bullet
except ModuleNotFoundError:
    pass


__BROWSERS__ = os.getenv('LIM_BROWSERS', 'firefox,chrome,safari').split(',')
CAFE_SERVER = os.getenv('LIM_CAFE_SERVER', '127.0.0.1')
CAFE_UI_PORT = os.getenv('LIM_CAFE_UI_PORT', 80)
CAFE_ADMIN_PORT = os.getenv('LIM_CAFE_ADMIN_PORT', 5001)
CAFE_API_VERSION = 'v1'
CAFE_ADMIN_URL = f'http://{ CAFE_SERVER }:{ CAFE_ADMIN_PORT }/{ CAFE_API_VERSION }'  # noqa
CAFE_API_URL = f'http://{ CAFE_SERVER }:{ CAFE_UI_PORT }/api/{ CAFE_API_VERSION }'  # noqa
CAFE_UI_URL = f'http://{ CAFE_SERVER }:{ CAFE_UI_PORT }/'
CAFE_DOCS_URL = 'https://cyberreboot.gitbook.io/packet-cafe'
LAST_SESSION_STATE = '.packet_cafe_last_session_id'
LAST_REQUEST_STATE = '.packet_cafe_last_request_id'

logger = logging.getLogger(__name__)


def add_packet_cafe_global_options(parser):
    """Add global packet_cafe options."""
    parser.add_argument(
        '--choose',
        action='store_true',
        dest='choose',
        default=False,
        help='Choose session and request (default: False)'
    )
    parser.add_argument(
        '--cafe-host',
        action='store',
        type=str,
        metavar='<cafe_host_ip>',
        dest='cafe_host_ip',
        default=CAFE_SERVER,
        help=('IP address for packet_cafe server '
              f'(Env: ``LIM_CAFE_HOST``; default: \'{ CAFE_SERVER }\')')
    )
    parser.add_argument(
        '--cafe-ui-port',
        action='store',
        type=int,
        metavar='<cafe_ui_port>',
        dest='cafe_ui_port',
        default=CAFE_UI_PORT,
        help=('TCP port for packet_cafe UI service '
              f'(Env: ``LIM_CAFE_UI_PORT``; default: { CAFE_UI_PORT })')
    )
    parser.add_argument(
        '--cafe-admin-port',
        action='store',
        type=int,
        metavar='<cafe_admin_port>',
        dest='cafe_admin_port',
        default=CAFE_ADMIN_PORT,
        help=('TCP port for packet_cafe admin service '
              f'(Env: ``LIM_CAFE_ADMIN_PORT``; default: { CAFE_ADMIN_PORT })')
    )
    return parser


def _valid_counter(value):
    """Counter must be integer starting with 1."""
    n = int(value)
    if n <= 0:
        raise argparse.ArgumentTypeError(
            f'counter must be positive integer (got { value })')
    return n


def choose_wisely(from_list=[], what='an item', cancel_throws_exception=False):
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
            raise RuntimeError(f'[-] cancelled chosing { what }')
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


def flatten(dict_item):
    """Flatten lists in dictionary values for better formatting."""
    flat_dict = {}
    for k, v in dict_item.items():
        flat_dict[k] = ",".join(v) if type(v) is list else v
    return flat_dict


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
        return [(flatten(i)) for i in results]
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


def get_worker_output(tool=None, counter=1, sess_id=None, req_id=None):
    """Get output from worker processing."""
    if tool is None:
        raise RuntimeError('[-] tool must not be None')
    if sess_id is None:
        raise RuntimeError('[-] sess_id must not be None')
    if req_id is None:
        raise RuntimeError('[-] req_id must not be None')
    url = (
        f'{ CAFE_API_URL }/results/'
        f'{ tool }/{ counter }/{ sess_id }/{ req_id }'
    )
    response = requests.request("GET", url)
    if response.status_code == 200:
        return response.text
    else:
        return None


def get_tools():
    """Get list of tools that produce output files."""
    workers = get_workers()
    tools = [
        worker['name'] for worker in workers
        if worker['viewableOutput']
    ]
    return tools


def get_workers():
    """Get details about workers."""
    response = requests.request("GET", f'{ CAFE_API_URL }/tools')
    if response.status_code == 200:
        return [flatten(worker) for worker in
                json.loads(response.text)['workers']]
    else:
        return None


def get_status(sess_id=None, req_id=None, raise_exception=True):
    """Get status for session ID + request ID."""
    if sess_id is None:
        if raise_exception:
            raise RuntimeError('[-] sess_id must not be None')
        else:
            return None
    if req_id is None:
        if raise_exception:
            raise RuntimeError('[-] req_id must not be None')
        else:
            return None
    url = f'{ CAFE_API_URL }/status/{ sess_id }/{ req_id }'
    response = requests.request("GET", url)
    if response.status_code == 200:
        return json.loads(response.text)
    elif raise_exception:
        raise RuntimeError(
            '[-] packet-cafe returned response: '
            f'{ response.status_code } { response.reason }'
        )
    else:
        return None


def get_raw(tool=None, counter=1, sess_id=None, req_id=None):
    """Get raw output from a specific tool, session, and request."""
    if tool is None:
        raise RuntimeError('[-] tool must not be None')
    if sess_id is None:
        raise RuntimeError('[-] sess_id must not be None')
    if req_id is None:
        raise RuntimeError('[-] req_id must not be None')
    url = f'{ CAFE_API_URL }/raw/{ tool }/{ counter }/{ sess_id }/{ req_id }'
    response = requests.request("GET", url)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        return None


def upload(fpath=None, sessionId=None):
    """Upload PCAP file to packet-cafe service for processing."""

    # Form data parameters
    # file: object: file to upload
    # sessionId: string: Session ID
    #
    if sessionId is None:
        sessionId = uuid.uuid4()
    # Only pass file basename to API
    fname = os.path.basename(fpath)
    with open(fpath, 'rb') as f:
        files = {'file': (fname, f.read())}
        data = {'sessionId': str(sessionId)}
        response = requests.post(f'{ CAFE_API_URL }/upload',
                                 files=files,
                                 data=data)
    if response.status_code == 201:
        result = json.loads(response.text)
        result['sess_id'] = str(sessionId)
        # Save state for later defaulting
        set_last_session_id(result['sess_id'])
        # NOTE(dittrich): Don't forget: 'req_id' is 'uuid' in result
        set_last_request_id(result['uuid'])
        time.sleep(3)
        return result
    else:
        raise RuntimeError(
            '[-] packet-cafe returned response: '
            f'{ response.status_code } { response.reason }'
        )


def stop(sess_id=None, req_id=None, raise_exception=True):
    """Stop jobs of a request ID."""
    if sess_id is None:
        raise RuntimeError('[-] sess_id must not be None')
    if req_id is None:
        raise RuntimeError('[-] req_id must not be None')
    url = f'{ CAFE_API_URL }/stop/{ sess_id }/{ req_id }'
    response = requests.request("GET", url)
    if response.status_code == 200:
        return json.loads(response.text)
    elif raise_exception:
        raise RuntimeError(
            '[-] packet-cafe returned response: '
            f'{ response.status_code } { response.reason }'
        )
    else:
        return None


def delete(sess_id=None, raise_exception=True):
    """Delete data for a session."""
    if sess_id is None:
        raise RuntimeError('[-] sess_id must not be None')
    url = f'{ CAFE_ADMIN_URL }/id/delete/{ sess_id }'
    response = requests.request("GET", url)
    if response.status_code == 200:
        return json.loads(response.text)
    elif raise_exception:
        raise RuntimeError(
            '[-] packet-cafe returned response: '
            f'{ response.status_code } { response.reason }'
        )
    else:
        return None


def track_progress(
    sess_id=None,
    req_id=None,
    debug=False,
    wait_only=False,
    elapsed=False
):
    """Track the progress of workers similar to the web UI."""
    if sess_id is None:
        raise RuntimeError('[-] sess_id must not be None')
    if req_id is None:
        raise RuntimeError('[-] req_id must not be None')
    workers = [worker['name'] for worker in get_workers()]  # noqa
    max_worker_len = max([len(i) for i in workers])
    timer = Timer()
    timer.start()
    reported = dict()
    last_status = {}
    while True:
        # Throttle API calls and give extra time to spin up initial workers
        time.sleep(5 if len(reported) == 0 else 2)
        status = get_status(sess_id=sess_id, req_id=req_id)
        # Worker status dictionaries are mixed into the dictionary
        # with a boolean flag. Filter it out.
        workers_reporting = [k for k in status.keys() if k != 'cleaned']
        states = dict()
        if debug and status != last_status:
            print(json.dumps(status), file=sys.stderr)
            last_status = status
        for worker in workers_reporting:
            states[status[worker]['state']] = True
            if (
                status[worker]['state'] not in ["Queued", "In progress"]
                and worker not in reported
            ):
                timer.lap(lap='now')
                if not wait_only:
                    print("[+] {0:{1}}".format(worker + ':',
                                               max_worker_len + 2) +
                          f"{ status[worker]['state'].lower() } " +
                          f"{ status[worker]['timestamp'] }" +
                          f" ({ timer.elapsed(end='now') })" if elapsed else "")  # noqa
                reported[worker] = True
        if len(reported) == len(workers):
            break


def get_last_session_id():
    """
    Return the last session ID if one is saved, else None.

    If the session does not exist in the server, deletes the
    state file and returns None.
    """
    if not os.path.exists(LAST_SESSION_STATE):
        return None
    sess_ids = get_session_ids()
    if sess_ids is None:
        return None
    with open(LAST_SESSION_STATE, 'r') as sf:
        sess_id = sf.read().strip()
        if sess_id in sess_ids:
            return sess_id
    os.remove(LAST_SESSION_STATE)
    return None


def set_last_session_id(sess_id=None):
    """
    Save the last session ID for later use.
    """
    if sess_id is None:
        return False
    try:
        with open(LAST_SESSION_STATE, 'w') as sf:
            sf.write(str(sess_id) + '\n')
    except:  # noqa
        return False
    return True


def get_last_request_id():
    """
    Return the last request ID if one is saved and it exists
    in the last session, else None.

    If the request does not exist in the server, deletes the
    state file and returns None.
    """
    try:
        sess_id = get_last_session_id()
    except RuntimeError:
        return None
    if not os.path.exists(LAST_REQUEST_STATE):
        return None
    with open(LAST_REQUEST_STATE, 'r') as sf:
        req_id = sf.read().strip()
    if get_status(
        sess_id=sess_id,
        req_id=req_id,
        raise_exception=False
    ) is not None:
        return req_id
    os.remove(LAST_REQUEST_STATE)
    return None


def set_last_request_id(req_id=None):
    """
    Save the last request ID for later use.
    """
    if req_id is None:
        return False
    try:
        with open(LAST_REQUEST_STATE, 'w') as sf:
            sf.write(str(req_id) + '\n')
    except:  # noqa
        return False
    return True


def check_remind_defaulting(arg=None, thing="argument"):
    """Log a reminder when argument is implicitly being reused."""
    if arg is not None:
        if str(arg) not in sys.argv:
            logger.info(f'[+] implicitly reusing { thing } { arg }')
    return arg


# vim: set ts=4 sw=4 tw=0 et :
