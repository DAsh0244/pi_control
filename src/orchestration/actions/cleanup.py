#! /usr/bin/env python
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
pi_control
cleanup.py
Author: Danyal Ahsanullah
Date: 6/26/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: action file that calls cleanup functions to cleanup hardware, close any open file descriptors.
Begins the shutdown state of the device.
"""

from libs.hal import hal_cleanup


# noinspection PyUnusedLocal
def cleanup(interface=None, params=None):
    """
    runs hal_cleanup() to safely reset pin configurations made over the course of usage.
    does not require any passed parameters.
    """
    print('cleaning')
    hal_cleanup()
    # stop conversions and logging
    # close any open file descriptors
    return 'success'
