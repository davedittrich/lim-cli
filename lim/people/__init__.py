# -*- coding: utf-8 -*-

import logging
from collections import OrderedDict

PEOPLE_DATABASE = 'people_db.sqlite'
PEOPLE_ROLES = [
    'STUDENT',
    'PROCTOR',
    'INSTRUCTOR',
    ]
PEOPLE_ATTRIBUTES = OrderedDict(
    {
        'person_id': 'Id',
        'short_name': 'Login name',
        'full_name': 'Full name',
        'role': 'Role',
        'email': 'Email address',
        'machine': 'Machine Id',
    }
)


logger = logging.getLogger(__name__)


# vim: set ts=4 sw=4 tw=0 et :
