# -*- coding: utf-8 -*-

import logging
import os
import sys

from pony.orm import *
from lim.people import (
    PEOPLE_ATTRIBUTES,
    PEOPLE_DATABASE,
    PEOPLE_ROLES,
)


def valid_email(address=''):
    """Simple email validator.

    Requires a string that looks like a valid email address in terms of
    a left hand side, an "@" character, and a right hand side with more
    than one "." character in it.  No other validation is done at this
    time.

    Args:
      address (str): Candidate email address.

    Returns:
      bool: Boolean value with test result.
    """

    try:
        lhs, rhs = address.split('@')
    except ValueError:
        return False
    if not lhs or rhs.find('.') <= 0:
        return False
    return True


logger = logging.getLogger(__name__)

# Not sure how to handle the way PonyORM does mappings
# without using side-effects from 'import' statement to
# share code across Cliff command classes.  Following
# the example in the PonyORM documentation as best as
# possible in the mean time:
# https://docs.ponyorm.org/working_with_relationships.html

db = Database()


class Person(db.Entity):
    person_id = PrimaryKey(int, auto=True)
    short_name = Required(str, unique=True)
    full_name = Required(str)
    role = Required(str)
    email = Required(str)
    machine = Optional('Machine', cascade_delete=True)


class Machine(db.Entity):
    machine_id = PrimaryKey(int, auto=True)
    user = Optional('Person')


# class Task(db.Entity):
#     task_id = PrimaryKey(int, auto=True)
#     person_id = Optional("Person")
#     task = Required(str)
#     done = Required(str)
#     time = Optional(str)


def db_connect(debug=False):
    """Ensure PonyORM database connection."""
    db_file = os.path.abspath(PEOPLE_DATABASE)
    db.bind('sqlite', db_file, create_db=True)
    logger.debug(f"[+] bound to database file '{db_file}'")
    if debug:
        sql_debug(True)
    db.generate_mapping(create_tables=True)
    return db


@db_session
def get_people_data():
    people_dicts = list(p.to_dict() for p in Person.select())
    return [
        list(pd.get(key, None) for key in PEOPLE_ATTRIBUTES)
        for pd in people_dicts
    ]


@db_session
def add_person(**attrs):
    if 'role' not in attrs:
        attrs['role'] = get_default_role()
    for key, value in attrs.items():
        if key not in PEOPLE_ATTRIBUTES:
            raise RuntimeError(f"[-] '{key}' is not a valid attribute")
        if key == 'email' and not valid_email(value):
            raise RuntimeError(f"[-] '{value}' is not a valid email address")
        if not value:
            raise RuntimeError(f"[-] '{value}' must not be null")

    return db.insert('Person',
                     **attrs,
                     # short_name=attrs.get('short_name'),
                     # full_name=attrs.get('full_name'),
                     # role=attrs.get('role', get_default_role()),
                     # email=email,
                     returning='person_id')


@db_session
def delete_person(**attrs):
    for key, value in attrs.items():
        if key not in PEOPLE_ATTRIBUTES:
            raise RuntimeError(f"[-] '{key}' is not a valid attribute")
        try:
            delete(p for p in Person if getattr(p, key) == value)
        except Exception as err:
            sys.exit(str(err))


@db_session
def update_person(person_id=None, args=[]):
    if person_id is None:
        raise RuntimeError("[-] no 'person_id' was specified")
    attrs = args_to_attrs(args)
    try:
        p = Person[person_id]
    except Exception as err:
        sys.exit(str(err))
    try:
        p.set(**attrs)
    except Exception as err:
        sys.exit(str(err))


@db_session
def get_people_columns():
    return PEOPLE_ATTRIBUTES.keys()
    # list(
    #     getattr(c, 'name')
    #     for c in db.schema.names['Person'].column_list
    # )


@db_session
def get_machines():
    return list(Machine.select())


@db_session
def get_machine_columns():
    return PEOPLE_ATTRIBUTES.keys()
    # list(
    #     getattr(c, 'name')
    #     for c in db.schema.names['Machine'].column_list
    # )


def get_default_role():
    return PEOPLE_ROLES[0]


def args_to_attrs(args=[], require_all=False):
    attrs = dict()
    invalid_keys = []
    for arg in args:
        key, value = arg.split('=')
        if key not in PEOPLE_ATTRIBUTES:
            invalid_keys.append(key)
        attrs[key] = value
    missing_keys = [
        key for key in PEOPLE_ATTRIBUTES.keys()
        if require_all and key not in attrs
    ]
    if len(invalid_keys):
        # CDO ALERT!
        # (It's like OCD, but the letters are in alphabetic order!)
        raise RuntimeError(
            "[-] invalid "
            f"attribute{'' if len(invalid_keys) == 1 else 's'}: "
            f"{','.join(invalid_keys)}")
    if len(missing_keys):
        # Woah! Deja vu!
        raise RuntimeError(
            "[-] missing attribute "
            f"key{'' if len(missing_keys) == 1 else 's'}: "
            f"{','.join(missing_keys)}")
    return attrs

# vim: set ts=4 sw=4 tw=0 et :
