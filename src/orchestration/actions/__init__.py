#! /usr/bin/env python
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
pi_control
actions/__init__.py
Author: Danyal Ahsanullah
Date: 6/25/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description:
"""
# prototype action function signature:
#
# def some_action(interface: obj, params: dict) -> str:
#     """
#     Action description
#
#     :param interface: base interface abstraction layer that is performing an action.
#     :param params: dictionary of the form
#     	{'param0':<val>, 'param1':<val>, ..., 'paramN':<val>}
#     """
#     condition = None
#     # stuff happens here -- eval and assign the desired value for condition
#     ...
#
#     return condition

import os
from typing import Iterable as _Iterable
from importlib import import_module as _import_module
from libs.utils import yamlobj
from enum import (
    Enum as _Enum,
    auto as _auto,
)


def _generate_statuses(conditions: _Iterable):
    for condition in conditions:
        setattr(Status, condition, _auto())


def _generate_action_map():
    return {module.upper(): getattr(_import_module('orchestration.actions.{0}'.format(module)), module)
            for module, ext in map(os.path.splitext, os.listdir(os.path.join(os.curdir, 'actions')))
            if not (module in {'readme', '__init__', '__pycache__'} or ext != '.py')}


action_map = _generate_action_map()


@yamlobj('!Action')
class Action:
    """
    actions are defined as having:
        a base function to be called
        a set of params to pass to function
    """
    # yaml_tag = '!Action'
    type = 'ACT'

    def __init__(self, name: str, params=None):
        self.name = name
        self.params = params
        self.action = action_map[self.name.upper()]

    def execute(self):
        return self.action(params=self.params)


# predefined states
def start_action(*args, **kwargs):
    return 'success'


def end_action(*args, **kwargs):
    return None


def error_action(*args, **kwargs):
    raise RuntimeError('An Error Occurred!')


# map implicit actions
action_map['ERROR'] = error_action
action_map['START'] = start_action
action_map['END'] = end_action

# default Action
START_ACTION = Action(name='START', params=None)
END_ACTION = Action(name='END', params=None)
ERROR_ACTION = Action(name='ERROR', params=None)


class Status(_Enum):
    success = _auto()
    failure = _auto()
    error = _auto()
