#! /usr/bin/env python
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
pi_control
reset_max.py
Author: Danyal Ahsanullah
Date: 6/26/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: 
"""
from libs.hal import actuator


def reset_max(interface=actuator, params=None):
    interface.reset_max()
    return 'success'
