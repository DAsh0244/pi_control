"""
pi_control
calibrate_strain.py
Author: Danyal Ahsanullah
Date: 7/24/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: 
"""

from libs.hal import StrainGauge, s1, actuator

actions = {'add_point', 'set_pos_rel', 'set_pos_abs', 'done'}

prompt = 'add_point:\n' \
         '\tusage: add_point <strain_value>' \
         '\ttake current measured strain and add to the calibration map' \
         'set_pos_rel:\n' \
         '\tusage: set_pos_rel <position_modifier>\n' \
         '\tmove actuator by described amount, negative values represent movement in the opposite direction\n' \
         'set_pos_abs\n' \
         '\tusage: set_pos_rel <position_modifier>\n' \
         '\tmove actuator to desired position\n' \
         'done:\n' \
         '\tusage: exists strain gauge calibration routine\n' \
         'enter command: '


def calibrate_strain(interface: StrainGauge = s1, params: dict = None) -> str:
    """
    returns either 'done' or 'error' as status condition

    :param interface: base interface abstraction layer that is performing an action.
    :param params: dictionary of the form {'param0':<val>, 'param1':<val>, ..., 'paramN':<val>}
    """
    condition = 'error'
    choice = input(prompt)
    while choice != 'done':
        while choice not in actions:
            choice = input(prompt)
        if choice == 'done':
            condition = 'done'
            break
        elif choice == 'add_point':
            cal_value = input('Enter the current strain percentage')
            interface.add_cal_point(cal_value)
            print(f'new strain of: {interface.read_adjusted_strain}')
        elif 'set_pos_rel' in choice:
            if actuator.units != 'raw':
                amt = float(choice.split()[1])
            else:
                amt = int(choice.split()[1])
            actuator.set_position(actuator.position + amt)
            print(f'unadjusted strain is: {interface.read_strain()}')
            print(f'adjusted strain is: {interface.read_adjusted_strain()}')
        elif 'set_pos_abs' in choice:
            if actuator.units != 'raw':
                amt = float(choice.split()[1])
            else:
                amt = int(choice.split()[1])
            actuator.set_position(amt)
            print(f'unadjusted strain is: {interface.read_strain()}')
            print(f'adjusted strain is: {interface.read_adjusted_strain()}')
    return condition
