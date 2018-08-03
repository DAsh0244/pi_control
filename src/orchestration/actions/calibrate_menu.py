#! /usr/bin/env python
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
pi_control
calibrate_menu.py
Author: Danyal Ahsanullah
Date: 7/24/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: action that launches other calibration routines
"""

prompt = '(s)train for strain gauge\n' \
         '(p)osition for position\n' \
         '(f)orce for force\n' \
         '(t <num>)emp for temperature\n' \
         'Enter choice for what to calibrate: '

temperature_sensors = {'t{num}' for num in range(1, 3 + 1)}

ret_vals = {'s': 'strain',
            'p': 'position',
            'f': 'force',
            # 't': 'temperature',
            }
ret_vals.update({k: f'temperature{k[1:]}' for k in temperature_sensors})


def calibrate_menu(interface: object = None, params: dict = None) -> str:
    """
    Action description

    :param interface: base interface abstraction layer that is performing an action.
    :param params: dictionary of the form {'param0':<val>, 'param1':<val>, ..., 'paramN':<val>}
    """
    condition = None
    choice = input(prompt).strip()
    while choice not in ret_vals.keys():
        choice = input(prompt).strip()
    return ret_vals[choice]
