#! /usr/bin/env python
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
pi_control
calibrate_force.py
Author: Danyal Ahsanullah
Date: 7/24/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: 
"""

from libs.hal import LoadCell, load_cell

choices = 'tcurdn'

prompt = f'current configuration is:\n' + \
         '\n'.join(['{}:{}'.format(k, v) for k, v in load_cell.configuration.items()]) + \
         '(t)are for taring\n' \
         '(c)alibrate for calibrate\n' \
         '(u)nits to swap units\n' \
         '(r)eport_rate <num> for setting report rate\n' \
         '(d)ecimal_places <num> for setting decimal places\n' \
         '(n)um_averages <num> for setting the nnumber of averages to aggergate\n' \
         'Enter choice: '


def calibrate_force(interface: LoadCell = load_cell, params: dict = None) -> str:
    """
    Action description

    :param interface: base interface abstraction layer that is performing an action.
    :param params: dictionary of the form {'param0':<val>, 'param1':<val>, ..., 'paramN':<val>}
    """
    condition = None
    choice = input(prompt).strip()
    while choice != 'done':
        while choice[0] not in choices:
            choice = input(prompt).strip()
        if choice == 't':
            interface.tare_device()
        elif choice[0] == 'u':
            current_units = interface.units
            interface.units = 'kg' if current_units != 'kg' else current_units
        elif choice[0] == 'd':
            interface.decimals = int(choice[1:])
        elif choice[0] == 'n':
            interface.num_avgs = int(choice[1:])
        elif choice[0] == 'r':
            interface.report_rate = int(choice[1:])
        else:
            condition = 'done'
            break
    return condition
