# -*- coding: utf-8 -*-

# See https://iqtlabs.gitbook.io/packet-cafe/design/api#api-v-1-tools

import argparse
import docker
import logging
import json
import os
import requests
# >> Issue: [B404:blacklist] Consider possible security implications associated
#           with subprocess module.
#    Severity: Low   Confidence: High
#    Location: lim/packet_cafe/__init__.py:11
#    More Info: https://bandit.readthedocs.io/en/
#    latest/blacklists/blacklist_imports.html#b404-import-subprocess
import subprocess  # nosec
import sys
import time
import uuid


from lim.utils import Timer
from urllib3.exceptions import ProtocolError


# TODO(dittrich): https://github.com/Mckinsey666/bullet/issues/2
# Workaround until bullet has Windows missing 'termios' fix.
try:
    from bullet import Bullet
except ModuleNotFoundError:
    pass


__BROWSERS__ = os.getenv('LIM_BROWSERS', 'firefox,chrome,safari').split(',')
NO_SESSIONS_MSG = '[-] packet-cafe server has no sessions'

logger = logging.getLogger(__name__)


def _valid_counter(value):
    """Counter must be integer starting with 1."""
    n = int(value)
    if n <= 0:
        raise argparse.ArgumentTypeError(
            f'counter must be positive integer (got { value })')
    return n


def choose_wisely(from_list=[], what='an item', cancel_throws_exception=False):
    if not len(from_list):
        raise RuntimeError(
            f'[-] caller did not provide { what } from which to choose')
    if not sys.stdout.isatty():
        raise RuntimeError('[-] no tty available')
    choices = ['<CANCEL>'] + from_list
    cli = Bullet(prompt=f'\nChoose { what }:',
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
            raise RuntimeError(f'[-] cancelled choosing { what }')
        else:
            return None
    return choice


def check_remind_defaulting(arg=None, thing="argument"):
    """Log a reminder when argument is implicitly being reused."""
    if arg is not None:
        if str(arg) not in sys.argv:
            logger.info(f'[+] implicitly reusing { thing } { arg }')
    return arg


def flatten(dict_item):
    """Flatten lists in dictionary values for better formatting."""
    flat_dict = {}
    for k, v in dict_item.items():
        flat_dict[k] = ",".join(v) if type(v) is list else v
    return flat_dict


def get_packet_cafe(app, parsed_args):
    """Return Packet_Cafe API object for this app.

    This function ensures that a single Packet_Cafe object
    is created for all of the "cafe" subcommands in a
    more DRY way.
    """
    if app.packet_cafe is None:
        app.packet_cafe = Packet_Cafe(
            sess_id=getattr(parsed_args, 'sess_id', None),
            cafe_host_ip=getattr(parsed_args, 'cafe_host_ip', None),
            cafe_admin_port=getattr(parsed_args, 'cafe_admin_port', None),
            cafe_ui_port=getattr(parsed_args, 'cafe_ui_port', None),
        )
    return app.packet_cafe


def containers_are_running():
    """Return boolean indicating running status of packet_cafe containers.

    NOTE(dittrich): By blindly checking the status of whatever set of
    containers are returned by Docker, there is a *small* possibility
    of a false positive here as docker-compose may still be bringing up
    containers when you check. To be safe, ensure that at minimum the
    ``ui``, ``web``, and ``admin`` containers are all running.

    See: https://iqtlabs.gitbook.io/packet-cafe/design/api
    """
    # TODO(dittrich): identify a way to tell how many containers *should* exist.  # noqa
    # Check out https://github.com/IQTLabs/packet_cafe/blob/master/workers/workers.json  # noqa
    #
    # NOTE(dittrich): Names may change?
    # This would be more robust if done via an API call.
    min_containers = [
        'packet_cafe_ui_1', 'packet_cafe_web_1', 'packet_cafe_admin_1'
    ]
    status = list(set([
                      c[1]
                      for c in get_containers(columns=['name', 'status'])
                      if len(c) == 2 and c[0] in min_containers
                      ]))
    return len(status) == 1 and 'running' in status


def get_containers(columns=['name', 'status']):
    """Get normalized metadata for packet_cafe Docker container."""
    client = docker.from_env()
    try:
        container_ids = [getattr(c, 'id') for c in client.containers.list()]
    except (requests.exceptions.ConnectionError, ProtocolError):
        raise RuntimeError(
            '[-] cannot connect to the Docker daemon: is it running?')
    containers = []
    for container_id in container_ids:
        container = client.containers.get(container_id)
        if container.labels.get(
            'com.docker.compose.project', ''
        ) == 'packet_cafe':
            containers.append([get_container_metadata(
                                 getattr(container, attr, None)
                               )
                               for attr in columns])
    return containers


def get_images(filter=None):
    """Return an array of JSON objects describing Docker images."""
    cmd = ['docker', 'images', '--format="{{json .}}"']
    results = get_output(cmd=cmd)
    #
    # The output from 'docker images' is a list of JSON objects that get
    # quotes added around the string, like this:
    #   '"{"Containers":"N/A","CreatedAt":"2020-08-22 17:26:57 -0700 PDT",
    #   "CreatedSince":"38 minutes ago","Digest":"\\u003cnone\\u003e",
    #   "ID":"f9f4e0d488ca","Repository":"davedittrich/packet_cafe_redis",
    #   "SharedSize":"N/A","Size":"29.8MB","Tag":"v0.2.6","UniqueSize":"N/A",
    #   "VirtualSize":"29.8MB"}"'
    # Strip off the quotes at the start and end of the line before converting.
    #
    images = [json.loads(r[1:-1]) for r in results]
    if filter is None:
        return images
    else:
        filtered_images = []
        for f in list(set(filter)):
            for i in images:
                if i['Repository'].startswith(f'{f}/'):
                    filtered_images.append(i)
                    next
        return filtered_images


def rm_images(images):
    """Remove Docker images.

    Returns input array with all successfully removed images, well, removed.
    (What did you expect?)
    """
    client = docker.from_env()
    removed_images = []
    for i in images:
        try:
            client.images.remove(i['ID'])
        except Exception:
            logger.info('[-] Failed to remove ID '
                        f"{i['ID']} ({i['Repository']})")
        else:
            removed_images.append(i)
    return removed_images


def get_container_metadata(item):
    """Extract desired metadata from Docker container object."""
    if type(item) is str:
        return item
    tags = getattr(item, 'tags', None)
    if tags is not None:
        return tags[0]
    else:
        return str(item)


class Packet_Cafe(object):
    """Class for interacting with a Packet Cafe server."""

    CAFE_HOST_IP = os.getenv('LIM_CAFE_HOST_IP', '127.0.0.1')
    CAFE_UI_PORT = os.getenv('LIM_CAFE_UI_PORT', 80)
    CAFE_ADMIN_PORT = os.getenv('LIM_CAFE_ADMIN_PORT', 5001)
    CAFE_API_VERSION = 'v1'
    CAFE_ADMIN_URL = f'http://{ CAFE_HOST_IP }:{ CAFE_ADMIN_PORT }/{ CAFE_API_VERSION }'  # noqa
    CAFE_API_URL = f'http://{ CAFE_HOST_IP }:{ CAFE_UI_PORT }/api/{ CAFE_API_VERSION }'  # noqa
    CAFE_UI_URL = f'http://{ CAFE_HOST_IP }:{ CAFE_UI_PORT }/'
    CAFE_GITHUB_URL = os.getenv('LIM_CAFE_GITHUB_URL',
                                'https://github.com/iqtlabs/packet_cafe.git')
    CAFE_DOCS_URL = 'https://iqtlabs.gitbook.io/packet-cafe'
    CAFE_DATA_DIR = os.getenv('VOL_PREFIX',
                              os.path.join(
                                  os.path.expanduser('~'),
                                  'packet_cafe_data')
                              )
    CAFE_REPO_DIR = os.getenv('LIM_CAFE_REPO_DIR',
                              os.path.join(
                                  os.path.expanduser('~'),
                                  'packet_cafe')
                              )
    CAFE_REPO_BRANCH = os.getenv('LIM_CAFE_REPO_BRANCH', 'master')
    CAFE_UI_PORT = os.getenv('LIM_CAFE_UI_PORT', 80)
    CAFE_SERVICE_NAMESPACE = os.getenv('LIM_CAFE_SERVICE_NAMESPACE', None)
    CAFE_SERVICE_VERSION = os.getenv('LIM_CAFE_SERVICE_VERSION', None)
    CAFE_TOOL_NAMESPACE = os.getenv('LIM_CAFE_TOOL_NAMESPACE', None)
    CAFE_TOOL_VERSION = os.getenv('LIM_CAFE_TOOL_VERSION', None)

    def __init__(
        self,
        sess_id=None,
        cafe_host_ip=None,
        cafe_admin_port=None,
        cafe_ui_port=None,
    ):
        if not containers_are_running():
            raise RuntimeError(
                '[-] the packet-cafe Docker containers do not appear to '
                'all be running\n[-] try "lim cafe containers show" command?'
            )
        self.sess_id = sess_id
        self.last_session_id = None
        self.last_request_id = None
        self.cafe_host_ip = cafe_host_ip
        self.cafe_admin_port = cafe_admin_port
        self.cafe_ui_port = cafe_ui_port

    def get_host_ip(self):
        return self.cafe_host_ip

    def get_admin_port(self):
        return self.cafe_admin_port

    def get_ui_port(self):
        return self.cafe_ui_port

    def get_docs_url(self):
        return self.CAFE_DOCS_URL

    def get_admin_url(self):
        return f'http://{ self.get_host_ip() }:{ self.get_admin_port() }/{ self.CAFE_API_VERSION }'  # noqa

    def get_api_url(self):
        return f'http://{ self.get_host_ip() }:{ self.get_ui_port() }/api/{ self.CAFE_API_VERSION }'  # noqa

    def get_ui_url(self):
        return f'http://{ self.get_host_ip() }:{ self.get_ui_port() }/'  # noqa

    def get_api_endpoints(self):
        """Get endpoints for packet-cafe API."""
        response = requests.request("GET", self.get_api_url())
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            return None

    def get_admin_endpoints(self):
        """Get endpoints for packet-cafe admin API."""
        response = requests.request("GET", self.get_admin_url())
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            return None

    def get_admin_info(self):
        """Get info for packet-cafe admin API."""
        response = requests.request("GET", f'{ self.get_admin_url() }/info')
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            return None

    def get_api_info(self):
        """Get info for packet-cafe API."""
        response = requests.request("GET", f'{ self.get_api_url() }/info')
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            return None

    def get_session_ids(self):
        """Get IDs from packet-cafe admin service."""
        url = f'{ self.get_admin_url() }/ids'
        response = requests.request("GET", url)
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            return None

    def get_requests(self, sess_id=None):
        """Get requests for a session from packet-cafe admin service."""
        # TODO(dittrich): Mock this for unit testing.
        # if sess_id == "ab7af73526814d58bf35f1399a5594b2":
        #     # return None
        #     return [
        #         {
        #             "id": "ab7af73526814d58bf35f1399a5594b2",
        #             "filename": "trace_ab7af73526814d58bf35f1399a5594b2_2020-04-09_23_38_56.pcap",  # noqa
        #             "tools": ["networkml", "mercury", "pcap_stats", "snort", "p0f", "pcapplot"],   # noqa
        #             "original_filename": "smallFlows.pcap"
        #         }
        #     ]

        url = f'{ self.get_api_url() }/ids/{ sess_id }'
        response = requests.request("GET", url)
        if response.status_code == 200:
            results = json.loads(response.text)
            return [(flatten(i)) for i in results]
        else:
            return None

    def get_request_ids(self, sess_id=None):
        """Get IDs from packet-cafe admin service."""
        results = self.get_requests(sess_id=sess_id)
        if results is not None:
            return [i['id'] for i in results]
        else:
            return None

    def get_sessions_requests_from_files(self):
        """Get all session and request IDs from /files API.

        Returns a dictionary keyed by session IDs with
        values being lists of associated request IDs.
        """
        response = requests.request("GET",
                                    f'{ self.get_admin_url() }/id/files')
        if response.status_code == 200:
            results = json.loads(response.text)
            ret_dict = dict()
            for r in results:
                # A line in /files output looks like this:
                # /files/{ sess_id }/{ req_id }/2015-06-07_capture-win2.pcap
                #
                sess_id, req_id = r.split('/')[2:4]
                if sess_id not in ret_dict:
                    ret_dict[sess_id] = []
                if req_id not in ret_dict[sess_id]:
                    ret_dict[sess_id].append(req_id)
            return ret_dict
        else:
            return None

    def get_files(self):
        """Get all files from packet-cafe admin service."""
        response = requests.request("GET",
                                    f'{ self.get_admin_url() }/id/files')
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            return None

    def get_results(self):
        """Get all results from packet-cafe admin service."""
        response = requests.request("GET",
                                    f'{ self.get_admin_url() }/id/results')
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            return None

    def get_worker_output(
        self,
        tool=None,
        counter=1,
        sess_id=None,
        req_id=None
    ):
        """Get output from worker processing."""
        if tool is None:
            raise RuntimeError('[-] tool must not be None')
        if sess_id is None:
            raise RuntimeError('[-] sess_id must not be None')
        if req_id is None:
            raise RuntimeError('[-] req_id must not be None')
        url = (
            f'{ self.get_api_url() }/results/'
            f'{ tool }/{ counter }/{ sess_id }/{ req_id }'
        )
        response = requests.request("GET", url)
        if response.status_code == 200:
            return response.text
        else:
            return None

    def get_tools(self):
        """Get list of tools that produce output files."""
        workers = self.get_workers()
        tools = [
            worker['name'] for worker in workers
            if (worker['viewableOutput']
                and 'contentType' in worker
                and worker['contentType'] == 'application/json'
                )
        ]
        return tools

    def get_workers(self):
        """Get details about workers."""
        response = requests.request("GET", f'{ self.get_api_url() }/tools')
        if response.status_code == 200:
            return [flatten(worker) for worker in
                    json.loads(response.text)['workers']]
        else:
            raise RuntimeError(
                '[-] packet-cafe returned response: '
                f'{ response.status_code } { response.reason }'
            )

    def get_status(
        self,
        sess_id=None,
        req_id=None,
        raise_exception=True
    ):
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
        url = f'{ self.get_api_url() }/status/{ sess_id }/{ req_id }'
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

    def get_raw(
        self,
        tool=None,
        counter=1,
        sess_id=None,
        req_id=None
    ):
        """Get raw output from a specific tool, session, and request."""
        if tool is None:
            raise RuntimeError('[-] tool must not be None')
        if sess_id is None:
            raise RuntimeError('[-] sess_id must not be None')
        if req_id is None:
            raise RuntimeError('[-] req_id must not be None')
        url = (
            f'{ self.get_api_url() }/raw/{ tool }/'
            f'{ counter }/{ sess_id }/{ req_id }'
        )
        response = requests.request("GET", url)
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            return None

    def upload(self, fpath=None, sess_id=None):
        """Upload PCAP file to packet-cafe service for processing."""

        # Form data parameters
        # file: object: file to upload
        # sessionId: string: Session ID
        #
        # NOTE(dittrich): Beware: "sess_id" vis "sessionId".
        if sess_id is None:
            sess_id = uuid.uuid4()
        # Only pass file basename to API
        fname = os.path.basename(fpath)
        with open(fpath, 'rb') as f:
            files = {'file': (fname, f.read())}
            # NOTE(dittrich): Beware: "sess_id" vis "sessionId".
            data = {'sessionId': str(sess_id)}
            response = requests.post(f'{ self.get_api_url() }/upload',
                                     files=files,
                                     data=data)
        if response.status_code == 201:
            result = json.loads(response.text)
            result['sess_id'] = str(sess_id)
            time.sleep(3)
            return result
        else:
            raise RuntimeError(
                '[-] packet-cafe returned response: '
                f'{ response.status_code } { response.reason }'
            )

    def stop(
        self,
        sess_id=None,
        req_id=None,
        raise_exception=True
    ):
        """Stop jobs of a request ID."""
        if sess_id is None:
            raise RuntimeError('[-] sess_id must not be None')
        if req_id is None:
            raise RuntimeError('[-] req_id must not be None')
        url = f'{ self.get_api_url() }/stop/{ sess_id }/{ req_id }'
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

    def delete(self, sess_id=None, raise_exception=True):
        """Delete data for a session."""
        if sess_id is None:
            raise RuntimeError('[-] sess_id must not be None')
        url = f'{ self.get_admin_url() }/id/delete/{ sess_id }'
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
        self,
        sess_id=None,
        req_id=None,
        debug=False,
        wait_only=False,
        ignore_errors=False,
        elapsed=False
    ):
        """Track the progress of workers similar to the web UI."""
        if sess_id is None:
            raise RuntimeError('[-] sess_id must not be None')
        if req_id is None:
            raise RuntimeError('[-] req_id must not be None')
        workers = [worker['name'] for worker in self.get_workers()]  # noqa
        max_worker_len = max([len(i) for i in workers])
        timer = Timer()
        timer.start()
        reported = dict()
        last_status = {}
        errors = False

        while True:
            # Throttle API calls and give extra time to spin up initial workers
            time.sleep(5 if len(reported) == 0 else 2)
            status = self.get_status(sess_id=sess_id, req_id=req_id)
            # Worker status dictionaries are mixed into the dictionary
            # with a boolean flag. Filter it out.
            workers_reporting = [k for k in status.keys() if k != 'cleaned']
            states = dict()
            if debug and status != last_status:
                try:
                    print(json.dumps(status), file=sys.stderr)
                except BrokenPipeError:
                    pass
                last_status = status
            for worker in workers_reporting:
                worker_state = status[worker]['state']
                states[worker_state] = True
                if (
                    worker_state not in ["Queued", "In progress"]
                    and worker not in reported
                ):
                    timer.lap(lap='now')
                    if not wait_only:
                        status_line = (
                            "[+] {0:{1}}".format(worker + ':',
                                                 max_worker_len + 2) +
                            f"{ worker_state.lower() } " +
                            f"{ status[worker]['timestamp'] }" +
                            (f" ({ timer.elapsed(end='now') })" if elapsed else "")  # noqa
                        )
                        try:
                            print(status_line)
                        except BrokenPipeError:
                            pass
                    reported[worker] = True
                if worker_state == "Error":
                    errors = True
            if (
                len(reported) == len(workers) or
                (errors and not ignore_errors)
            ):
                break
        return not errors

    def get_session_id(
        self,
        sess_id=None,
        reuse_session=True,
        choose=False,
        generate=False,
    ):
        """Ensure a session_id is available.

        Priority for obtaining the session ID is:
        1. Specified on the command line (i.e., passed as "sess_id");
        2. Defaulting to the last-used session ID;
        3. Chosen from existing sessions (if requested to choose);
        4. Generating a new session ID (if requested).
        """
        _sess_id = None
        if self.last_session_id is None:
            self.last_session_id = self.get_last_session_id()
        if sess_id is not None:
            _sess_id = sess_id
        elif (
            self.last_session_id is not None
            and reuse_session
            and not choose
        ):
            logger.info('[+] implicitly reusing last '
                        f'session ID { self.last_session_id }')
            _sess_id = self.last_session_id
        if _sess_id is None and choose:
            ids = self.get_session_ids()
            _sess_id = choose_wisely(
                from_list=ids,
                what="a session",
                cancel_throws_exception=True
            )
        if _sess_id is None and generate:
            _sess_id = uuid.uuid4()
        if sess_id is None and _sess_id is None:
            raise RuntimeError(
                "[-] session ID not provided" +
                (" - use '--choose'?" if sys.stdout.isatty() else "")
            )
        return _sess_id

    def get_last_session_id(self):
        """Return the last session ID if one is saved, else None."""
        response = self.get_api_info()
        return response['last_session_id']

    def is_active_session_id(self, sess_id=None):
        sess_ids = self.get_session_ids()
        return sess_id in sess_ids

    def get_request_id(
        self,
        sess_id=None,
        req_id=None,
        choose=False
    ):
        """Get a request ID from a session.

        Priority for obtaining the request ID is:
        1. Specified on the command line (i.e., passed as "req_id");
        2. Defaulting to the last used request ID (if not asked to choose);
        3. Selected by the user interactively (if asked to choose);
        4. Return None.
        """
        if req_id is not None and choose:
            raise RuntimeError(
                '[-] a req_id was passed and --choose selected; '
                'do one or the other')
        _req_id = None
        if self.last_request_id is None:
            self.last_request_id = self.get_last_request_id()
        if req_id is None:
            if not choose:
                logger.info('[+] implicitly reusing last '
                            f'request ID { self.last_request_id }')
                _req_id = self.last_request_id
            else:
                if sess_id is None:
                    if self.last_session_id is None:
                        raise RuntimeError(
                            '[-] sess_id required to identify req_id choices')
                    sess_id = self.last_session_id
                request_ids = self.get_request_ids(sess_id=sess_id)
                _req_id = choose_wisely(
                    from_list=request_ids,
                    what="a request",
                    cancel_throws_exception=True
                )
        if req_id is None and _req_id is None:
            raise RuntimeError(
                "[-] request ID not provided" +
                (" - use '--choose'?" if sys.stdout.isatty() else "")
            )
        return _req_id

    def get_last_request_id(self):
        """
        Return the last request ID if one is saved and it exists
        in the last session, else None.
        """
        response = self.get_api_info()
        return response['last_request_id']

    def is_valid_request_id(self, sess_id=None, req_id=None):
        """Return True if req_id is found in Session sess_id."""
        if sess_id is None or req_id is None:
            return False
        return self.get_status(
            sess_id=sess_id,
            req_id=req_id,
            raise_exception=False
        ) is not None


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
        default=Packet_Cafe.CAFE_HOST_IP,
        help=('IP address for packet_cafe server '
              '(Env: ``LIM_CAFE_HOST``; '
              f'default: \'{ Packet_Cafe.CAFE_HOST_IP }\')')
    )
    parser.add_argument(
        '--cafe-ui-port',
        action='store',
        type=int,
        metavar='<cafe_ui_port>',
        dest='cafe_ui_port',
        default=Packet_Cafe.CAFE_UI_PORT,
        help=('TCP port for packet_cafe UI service '
              '(Env: ``LIM_CAFE_UI_PORT``; '
              f'default: { Packet_Cafe.CAFE_UI_PORT })')
    )
    parser.add_argument(
        '--cafe-admin-port',
        action='store',
        type=int,
        metavar='<cafe_admin_port>',
        dest='cafe_admin_port',
        default=Packet_Cafe.CAFE_ADMIN_PORT,
        help=('TCP port for packet_cafe admin service '
              '(Env: ``LIM_CAFE_ADMIN_PORT``; '
              f'default: { Packet_Cafe.CAFE_ADMIN_PORT })')
    )
    return parser


def add_docker_global_options(parser):
    """Add global Docker options."""
    parser.add_argument(
        '--docker-service-namespace',
        action='store',
        metavar='<service_namespace>',
        dest='docker_service_namespace',
        default=Packet_Cafe.CAFE_SERVICE_NAMESPACE,
        help=('Namespace for Packet Café service containers '
              '(Env: ``LIM_CAFE_SERVICE_NAMESPACE``; '
              f'default: { Packet_Cafe.CAFE_SERVICE_NAMESPACE })')
    )
    parser.add_argument(
        '--docker-service-version',
        action='store',
        metavar='<service_version>',
        dest='docker_service_version',
        default=Packet_Cafe.CAFE_SERVICE_VERSION,
        help=('Version (tag) for Packet Café service containers '
              '(Env: ``LIM_CAFE_SERVICE_VERSION``; '
              'default: "latest")')
    )
    parser.add_argument(
        '--docker-tool-namespace',
        action='store',
        metavar='<tool_namespace>',
        dest='docker_tool_namespace',
        default=Packet_Cafe.CAFE_TOOL_NAMESPACE,
        help=('Namespace for Packet Café tool containers '
              '(Env: ``LIM_CAFE_TOOL_NAMESPACE``; '
              f'default: { Packet_Cafe.CAFE_TOOL_NAMESPACE })')
    )
    parser.add_argument(
        '--docker-tool-version',
        action='store',
        metavar='<tool_version>',
        dest='docker_tool_version',
        default=Packet_Cafe.CAFE_TOOL_VERSION,
        help=('Version (tag) for Packet Café tool containers '
              '(Env: ``LIM_CAFE_TOOL_VERSION``; '
              'default: "latest")')
    )
    parser.add_argument(
        '--packet-cafe-github-url',
        action='store',
        metavar='<github_url>',
        dest='packet_cafe_github_url',
        default=Packet_Cafe.CAFE_GITHUB_URL,
        help=('URL for packet_cafe GitHub repository '
              '(Env: ``LIM_CAFE_GITHUB_URL``; '
              f'default: { Packet_Cafe.CAFE_GITHUB_URL })')
    )
    parser.add_argument(
        '--packet-cafe-repo-dir',
        action='store',
        metavar='<repo_dir>',
        dest='packet_cafe_repo_dir',
        default=Packet_Cafe.CAFE_REPO_DIR,
        help=('Directory holding clone of packet_cafe repository '
              '(Env: ``LIM_CAFE_REPO_DIR``; '
              f'default: { Packet_Cafe.CAFE_REPO_DIR })')
    )
    parser.add_argument(
        '--packet-cafe-repo-branch',
        action='store',
        metavar='<repo_branch>',
        dest='packet_cafe_repo_branch',
        default=Packet_Cafe.CAFE_REPO_BRANCH,
        help=('Branch of packet_cafe repository to use '
              '(Env: ``LIM_CAFE_REPO_BRANCH``; '
              f'default: { Packet_Cafe.CAFE_REPO_BRANCH })')
    )
    return parser


def get_output_realtime(cmd=['echo', 'NO COMMAND SPECIFIED'],
                        cwd=os.getcwd(),
                        env=os.environ,
                        stderr=subprocess.STDOUT,
                        shell=False):
    """Use subprocess.Popen() to track process output in realtime"""
    p = subprocess.Popen(  # nosec
            cmd,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=stderr,
            shell=shell
        )
    for char in iter(p.stdout.readline, b''):
        sys.stdout.write(char.decode('utf-8'))
    p.stdout.close()
    return p.wait()


def get_output(
    cmd=['echo', 'NO COMMAND SPECIFIED'],
    cwd=os.getcwd(),
    stderr=subprocess.STDOUT,
    shell=False
):
    """Use subprocess.check_ouput to run subcommand"""
    output = subprocess.check_output(  # nosec
            cmd,
            cwd=cwd,
            stderr=stderr,
            shell=shell
        ).decode('UTF-8').splitlines()
    return output

# vim: set ts=4 sw=4 tw=0 et :
