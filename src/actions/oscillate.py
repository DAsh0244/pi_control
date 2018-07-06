#! /usr/bin/env python
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
pi_control
oscillate.py
Author: Danyal Ahsanullah
Date: 6/28/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: 
"""

from libs.hal import actuator
from time import perf_counter


def oscillate(interface=actuator, params=None, nxt=None):
    """
    Moves from thresholds described in params dict with keys of 'low_pos', 'high_pos'.
    Movement speed is defined in params dict with the 'speed' key.
    Adaptive controller is optionally specified with the 'controller' key.
    The ability to end oscillation at the closest threshold (low or high) is available with the 'reset_closest' key,
        which expects a boolean True or False value. If not specified, defaults to False
    Mutually exclusive number of oscillations and timeout are also optional params. if both are specified,
    it will stop at whatever comes first.
        - timeout is specified with the 'timeout' key and expects a float
        - repetitions is specified with the 'repetitions' key and expects an int
    """
    if nxt is None:
        nxt = {'success': None}
    condition = 'success'
    low_pos = params['low_pos']
    high_pos = params['high_pos']
    timeout = params.get('timeout', float('inf'))
    repetitions = params.get('repetitions', float('inf'))
    controller = params.get('controller', None)
    repeats = 0
    start = perf_counter()
    while ((perf_counter() - start) < timeout) or (repeats < repetitions):
        interface.set_position(low_pos)
        interface.set_position(high_pos)
    if params.get('reset_closest', False):
        # is closer to lower spot than higher spot
        if abs(interface.position - low_pos) > abs(interface.position - high_pos):
            interface.set_position(low_pos)
        else:
            interface.set_position(low_pos)
    return nxt[condition]
