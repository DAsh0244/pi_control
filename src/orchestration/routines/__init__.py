#! /usr/bin/env python
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
pi_control
routines/__init__.py
Author: Danyal Ahsanullah
Date: 6/11/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: import available routines here
"""

from typing import Union, Dict

from libs.utils import yamlobj
from orchestration.actions import START_ACTION, END_ACTION, ERROR_ACTION


@yamlobj('!Routine')
class Routine:
    # yaml_tag = '!Routine'
    type = 'RTN'

    def __init__(self, name: str, len_units: str, force_units: str, actions: Dict[str, Union[None, Dict[str, Union[None, str, int, float]]]],
                 transitions=None, exec=True, output: str = 'stdout'):
        self.name = name
        self.len_units = len_units
        self.force_units = force_units
        self.exec = exec
        self.actions = actions
        self.actions['START'] = START_ACTION
        self.actions['END'] = END_ACTION
        self.actions.setdefault('ERROR', ERROR_ACTION)
        self.output = output
        self.transitions = transitions if transitions is not None else {'START': {'*': 'ERROR'}}
        self.transitions.setdefault('START', {'*': 'ERROR'})
        # self.transitions.setdefault('ERROR', {'*': 'END'})
