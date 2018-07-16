#! /usr/bin/env python
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
pi_control
set_pos.py
Author: Danyal Ahsanullah
Date: 6/26/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: 
"""

from libs.hal import actuator


def set_pos(interface=actuator, params=(actuator.pos_limit_low + actuator.pos_limit_high) >> 1):
    interface.set_position(*params)
    return 'success'
