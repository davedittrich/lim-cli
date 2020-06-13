# -*- coding: utf-8 -*-

# See https://cyberreboot.gitbook.io/packet-cafe/design/api#api-v-1-tools

import argparse
import docker
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
# CAFE_SERVER = os.getenv('LIM_CAFE_SERVER', '127.0.0.1')
# CAFE_UI_PORT = os.getenv('LIM_CAFE_UI_PORT', 80)
# CAFE_ADMIN_PORT = os.getenv('LIM_CAFE_ADMIN_PORT', 5001)
# CAFE_API_VERSION = 'v1'
# CAFE_ADMIN_URL = f'http://{ CAFE_SERVER }:{ CAFE_ADMIN_PORT }/{ CAFE_API_VERSION }'  # noqa
# CAFE_API_URL = f'http://{ CAFE_SERVER }:{ CAFE_UI_PORT }/api/{ CAFE_API_VERSION }'  # noqa
# CAFE_UI_URL = f'http://{ CAFE_SERVER }:{ CAFE_UI_PORT }/'
# CAFE_DOCS_URL = 'https://cyberreboot.gitbook.io/packet-cafe'
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
        default=Packet_Cafe.get_default_server(),
        help=('IP address for packet_cafe server '
              '(Env: ``LIM_CAFE_HOST``; '
              f'default: \'{ Packet_Cafe.get_default_server() }\')')
    )
    parser.add_argument(
        '--cafe-ui-port',
        action='store',
        type=int,
        metavar='<cafe_ui_port>',
        dest='cafe_ui_port',
        default=Packet_Cafe.get_default_ui_port(),
        help=('TCP port for packet_cafe UI service '
              '(Env: ``LIM_CAFE_UI_PORT``; '
              f'default: { Packet_Cafe.get_default_ui_port() })')
    )
    parser.add_argument(
        '--cafe-admin-port',
        action='store',
        type=int,
        metavar='<cafe_admin_port>',
        dest='cafe_admin_port',
        default=Packet_Cafe.get_default_admin_port(),
        help=('TCP port for packet_cafe admin service '
              '(Env: ``LIM_CAFE_ADMIN_PORT``; '
              f'default: { Packet_Cafe.get_default_admin_port() })')
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
    if not len(from_list):
        raise RuntimeError('[-] nothing provided from which to choose')
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
            cafe_server=getattr(parsed_args, 'cafe_server', None),
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

    See: https://cyberreboot.gitbook.io/packet-cafe/design/api
    """
    # TODO(dittrich): identify a way to tell how many containers *should* exist.  # noqa
    # NOTE(dittrich): Names may change?
    # This would be more robust if done via an API call.
    min_containers = [
        'packet_cafe_ui_1', 'packet_cafe_web_1', 'packet_cafe_admin_1'
    ]
    status = list(set([
                      c[1]
                      for c in get_containers(columns=['name', 'status'])
                      if c[0] in min_containers
                      ]))
    return len(status) == 1 and 'running' in status


def get_containers(columns=['name', 'status']):
    """Get normalized metadata for packet_cafe Docker container."""
    client = docker.from_env()
    container_ids = [getattr(c, 'id') for c in client.containers.list()]
    containers = []
    for container_id in container_ids:
        container = client.containers.get(container_id)
        containers.append([get_container_metadata(
                             getattr(container, attr, None)
                           )
                           for attr in columns
                           if container.labels.get(
                               'com.docker.compose.project', '')
                           == 'packet_cafe'
                           ])
    return containers


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
    """Class for interactive with a Packet Cafe server."""

    CAFE_SERVER = os.getenv('LIM_CAFE_SERVER', '127.0.0.1')
    CAFE_UI_PORT = os.getenv('LIM_CAFE_UI_PORT', 80)
    CAFE_ADMIN_PORT = os.getenv('LIM_CAFE_ADMIN_PORT', 5001)
    CAFE_API_VERSION = 'v1'
    CAFE_ADMIN_URL = f'http://{ CAFE_SERVER }:{ CAFE_ADMIN_PORT }/{ CAFE_API_VERSION }'  # noqa
    CAFE_API_URL = f'http://{ CAFE_SERVER }:{ CAFE_UI_PORT }/api/{ CAFE_API_VERSION }'  # noqa
    CAFE_UI_URL = f'http://{ CAFE_SERVER }:{ CAFE_UI_PORT }/'
    CAFE_DOCS_URL = 'https://cyberreboot.gitbook.io/packet-cafe'

    def __init__(
        self,
        sess_id=None,
        cafe_server=None,
        cafe_admin_port=None,
        cafe_ui_port=None,
    ):
        if not containers_are_running():
            raise RuntimeError(
                '[-] the packet-cafe Docker containers do not appear to'
                'all be running\n[-] try "lim cafe containers" command?'
            )
        self.sess_id = sess_id
        self.cafe_server = self.CAFE_SERVER if cafe_server is None else cafe_server  # noqa
        self.cafe_admin_port = self.CAFE_ADMIN_PORT if cafe_admin_port is None else cafe_admin_port  # noqa
        self.cafe_ui_port = self.CAFE_UI_PORT if cafe_ui_port is None else cafe_ui_port  # noqa
        self.cafe_admin_url = f'http://{ self.cafe_server }:{ self.cafe_admin_port }/{ self.CAFE_API_VERSION }'  # noqa
        self.cafe_api_url = f'http://{ self.cafe_server }:{ self.cafe_ui_port }/api/{ self.CAFE_API_VERSION }'  # noqa
        self.cafe_ui_url = f'http://{ self.cafe_server }:{ self.cafe_ui_port }/'  # noqa
        self.cafe_docs_url = self.CAFE_DOCS_URL

    @classmethod
    def get_default_server(cls):
        return cls.CAFE_SERVER

    @classmethod
    def get_default_admin_port(cls):
        return cls.CAFE_ADMIN_PORT

    @classmethod
    def get_default_ui_port(cls):
        return cls. CAFE_UI_PORT

    @classmethod
    def get_default_admin_url(cls):
        return cls.CAFE_ADMIN_URL

    @classmethod
    def get_default_api_url(cls):
        return cls.CAFE_API_URL

    @classmethod
    def get_default_ui_url(cls):
        return cls.CAFE_UI_URL

    @classmethod
    def get_default_docs_url(cls):
        return cls.CAFE_DOCS_URL

    def get_api_endpoints(self):
        """Get endpoints for packet-cafe API."""
        response = requests.request("GET", self.cafe_api_url)
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            return None

    def get_admin_endpoints(self):
        """Get endpoints for packet-cafe admin API."""
        response = requests.request("GET", self.cafe_admin_url)
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            return None

    def get_admin_info(self):
        """Get info for packet-cafe admin API."""
        response = requests.request("GET", f'{ self.cafe_admin_url }/info')
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            return None

    def get_api_info(self):
        """Get info for packet-cafe API."""
        response = requests.request("GET", f'{ self.cafe_api_url }/info')
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            return None

    def get_session_ids(self):
        """Get IDs from packet-cafe admin service."""
        url = f'{ self.cafe_admin_url }/ids'
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
        #             "tools": ["networkml", "mercury", "pcap-stats", "snort", "p0f", "pcapplot"],   # noqa
        #             "original_filename": "smallFlows.pcap"
        #         }
        #     ]

        url = f'{ self.cafe_api_url }/ids/{ sess_id }'
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

    def get_files(self):
        """Get all files from packet-cafe admin service."""
        response = requests.request("GET", f'{ self.cafe_admin_url }/id/files')
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            return None

    def get_results(self):
        """Get all results from packet-cafe admin service."""
        response = requests.request("GET", f'{ self.cafe_admin_url }/id/results')  # noqa
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
            f'{ self.cafe_api_url }/results/'
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
            if worker['viewableOutput']
        ]
        return tools

    def get_workers(self):
        """Get details about workers."""
        response = requests.request("GET", f'{ self.cafe_api_url }/tools')
        if response.status_code == 200:
            return [flatten(worker) for worker in
                    json.loads(response.text)['workers']]
        else:
            return None

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
        url = f'{ self.cafe_api_url }/status/{ sess_id }/{ req_id }'
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
            f'{ self.cafe_api_url }/raw/{ tool }/'
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
            response = requests.post(f'{ self.cafe_api_url }/upload',
                                     files=files,
                                     data=data)
        if response.status_code == 201:
            result = json.loads(response.text)
            result['sess_id'] = str(sess_id)
            # Save state for later defaulting
            self.set_last_session_id(result['sess_id'])
            # NOTE(dittrich): Don't forget: 'req_id' is 'uuid' in result
            self.set_last_request_id(result['uuid'])
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
        url = f'{ self.cafe_api_url }/stop/{ sess_id }/{ req_id }'
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
        url = f'{ self.cafe_admin_url }/id/delete/{ sess_id }'
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
        while True:
            # Throttle API calls and give extra time to spin up initial workers
            time.sleep(5 if len(reported) == 0 else 2)
            status = self.get_status(sess_id=sess_id, req_id=req_id)
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
                        status_line = (
                            "[+] {0:{1}}".format(worker + ':',
                                                 max_worker_len + 2) +
                            f"{ status[worker]['state'].lower() } " +
                            f"{ status[worker]['timestamp'] }" +
                            (f" ({ timer.elapsed(end='now') })" if elapsed else "")  # noqa
                        )
                        print(status_line)
                    reported[worker] = True
            if len(reported) == len(workers):
                break

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
        last_sess_id = self.get_last_session_id()
        _id = None
        if sess_id is not None:
            _id = sess_id
        elif last_sess_id is not None and reuse_session:
            logger.info('[+] implicitly reusing last '
                        f'session ID { last_sess_id }')
            _id = last_sess_id
        elif choose:
            ids = self.get_session_ids()
            _id = choose_wisely(
                from_list=ids,
                what="session",
                cancel_throws_exception=True
            )
        elif generate:
            _id = uuid.uuid4()
        if sess_id is None and _id is None:
            raise RuntimeError(
                "[-] session ID not provided - use '--choose'?")
        return _id

    def get_last_session_id(self):
        """Return the last session ID if one is saved, else None.

        If the session does not exist in the server, deletes the
        state file and returns None.
        """
        if not os.path.exists(LAST_SESSION_STATE):
            return None
        sess_ids = self.get_session_ids()
        if sess_ids is None:
            return None
        with open(LAST_SESSION_STATE, 'r') as sf:
            sess_id = sf.read().strip()
            if sess_id in sess_ids:
                return sess_id
        os.remove(LAST_SESSION_STATE)
        return None

    def set_last_session_id(self, sess_id=None):
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

    def get_request_id(self, sess_id=None, req_id=None, choose=False):
        """Get a request ID from a session.

        Priority for obtaining the request ID is:
        1. Specified on the command line (i.e., passed as "req_id");
        2. Defaulting to the last used request ID (if not asked to choose);
        3. Selected by the user interactively (if asked to choose);
        4. return None.
        """
        last_req_id = self.get_last_request_id()
        _id = None
        if req_id is not None:
            _id = req_id
        if choose:
            _id = choose_wisely(
                from_list=self.get_request_ids(sess_id=sess_id),
                what="a request",
                cancel_throws_exception=True
            )
        elif last_req_id is not None:
            logger.info('[+] implicitly reusing last '
                        f'request ID { last_req_id }')
            _id = last_req_id
        if req_id is None and _id is None:
            raise RuntimeError(
                "[-] request ID not provided - use '--choose'?")
        return _id

    def get_last_request_id(self):
        """
        Return the last request ID if one is saved and it exists
        in the last session, else None.

        If the request does not exist in the server, deletes the
        state file and returns None.
        """
        try:
            sess_id = self.get_last_session_id()
        except RuntimeError:
            return None
        if not os.path.exists(LAST_REQUEST_STATE):
            return None
        with open(LAST_REQUEST_STATE, 'r') as sf:
            req_id = sf.read().strip()
        if self.get_status(
            sess_id=sess_id,
            req_id=req_id,
            raise_exception=False
        ) is not None:
            return req_id
        os.remove(LAST_REQUEST_STATE)
        return None

    def set_last_request_id(self, req_id=None):
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


# vim: set ts=4 sw=4 tw=0 et :
