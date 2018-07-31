# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
pi_control
position_lut.py
Author: Danyal Ahsanullah
Date: 7/31/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: 
"""

from math import ceil
from itertools import repeat, chain
from typing import Union, Dict, Iterable
from libs.hal import actuator, Actuator


# action_params: Dict[str, Union[str, int, float, Iterable]]


def position_lut(interface: Actuator = actuator,
                 params: Union[Dict[str, Union[str, int, float, Iterable]], None] = None) -> str:
    """
    Moves the actuator to each position sequentially.

    :param interface: Actuator instance to control actuator.
    :param params: dictionary of the form
        {
         'positions': Iterable[Union[int,float]],
         'speeds':Union[Iterable[Union[int,float]],None],
         'units': str,
         'cycles': number of time to repeat the table,
         }

    :return condition string of value:
        'error': error condition
        'success': moved to next position in LUT
        'done': finished all entries in LUT
    """
    condition = 'error'
    units = params.get('units', interface.units)
    positions = list(map(interface.convert_units[units], params['positions']))
    if params.get('cycles', False):
        positions = list(chain.from_iterable(repeat(positions, params['cycles'])))
    speeds = params.get('speeds', None)
    if speeds is None:
        speeds = interface.speed_controller.default_val
        # speeds = list(map(interface.convert_units[units], speeds))
    speeds = repeat(speeds, len(positions))
    for pos, speed in zip(positions, speeds):
        interface.set_position(pos, speed)
    else:
        condition = 'done'
    return condition
