#! /usr/bin/env python
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
pi_control
__init__.py.py
Author: Danyal Ahsanullah
Date: 7/13/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: 
"""

import yaml
from orchestration.actions import action_map, Action
from orchestration.routines import Routine

if __name__ == '__main__':
    from pprint import pprint

    pprint(action_map)
    with open('../../test/test_config.yaml') as file:
        pprint(yaml.load(file))
