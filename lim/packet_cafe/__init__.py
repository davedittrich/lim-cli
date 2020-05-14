# -*- coding: utf-8 -*-

# See https://cyberreboot.gitbook.io/packet-cafe/design/api#api-v-1-tools

import json
import requests
import uuid

CAFE_SERVER = '127.0.0.1'
CAFE_PORT = 5001
CAFE_API_VERSION = 'v1'
CAFE_ADMIN_URL = f'http://{CAFE_SERVER}:{CAFE_PORT}/{CAFE_API_VERSION}'
CAFE_API_URL = f'http://{CAFE_SERVER}/api/{CAFE_API_VERSION}'


def get_ids():
    """Get IDs from packet-cafe admin service."""
    url = f'{CAFE_ADMIN_URL}/ids'
    response = requests.request("GET", url)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        return None


def get_ids_for_session(sess_id=None):
    """Get IDs from packet-cafe admin service."""
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

    url = f'{CAFE_API_URL}/ids/{sess_id}'
    response = requests.request("GET", url)
    if response.status_code == 200:
        results = json.loads(response.text)
        return [(i) for i in results]
    else:
        return None


def get_files():
    """Get all files from packet-cafe admin service."""
    response = requests.request("GET", f'{CAFE_ADMIN_URL}/id/files')
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        return None


def get_results():
    """Get all results from packet-cafe admin service."""
    response = requests.request("GET", f'{CAFE_ADMIN_URL}/id/results')
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        return None


def get_status(sess_id=None, req_id=None):
    """Get status for session ID + request ID."""
    if sess_id is None:
        raise RuntimeError(f'sess_id must not be None')
    if req_id is None:
        raise RuntimeError(f'req_id must not be None')
    url = f'{ CAFE_API_URL }/status/{ sess_id }/{ req_id }'
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
        response = requests.post(f'{CAFE_API_URL}/upload',
                                 files=files,
                                 data=data)
    if response.status_code == 201:
        return json.loads(response.text)
    else:
        return None


__all__ = [
    CAFE_SERVER,
    CAFE_PORT,
    CAFE_API_VERSION,
    CAFE_ADMIN_URL,
    CAFE_API_URL,
    get_ids,
    get_files,
    get_results,
    upload,
]


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
