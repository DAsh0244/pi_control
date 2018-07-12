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
from enum import (
    Enum as _Enum,
    auto as _auto,
)

from libs.utils import nop
from .set_pos import set_pos
from .cleanup import cleanup
from .calibrate import calibrate
from .reset_max import reset_max
from .reset_min import reset_min


class Status(_Enum):
    success = _auto()
    failure = _auto()
    error = _auto()


actions = {'RESET_MIN': reset_min,
           'RESET_MAX': reset_max,
           'GOTO_POS': set_pos,
           'CLEANUP': cleanup,
           None: nop,
           'None': nop,
           }


def generate_statuses(conditions: _Iterable):
    for condition in conditions:
        setattr(Status, condition, _auto())


def generate_actions():
    for module in os.listdir(os.curdir):
        if module in {'readme.md', '__init__.py'}:
            continue
        actions[module.upper()] = _import_module('{0}.{0}'.format(module))
