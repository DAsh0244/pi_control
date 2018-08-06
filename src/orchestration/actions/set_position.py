# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
pi_control
calibrate.py
Author: Danyal Ahsanullah
Date: 6/26/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: 
"""
from libs.hal import Actuator, actuator

WAIT_TIMEOUT = 2


def set_position(interface: Actuator = actuator, params=None):
    """
    allow manual setting of position of actuator.
    """
    speed_ctrl = interface.speed_controller
    pos_sense = interface.position_sensor
    speed_ctrl.set_voltage(speed_ctrl.stop)
    done = 'n'
    current_speed = speed_ctrl.value
    try:
        while done != 'y':
            current_pos = interface.position
            current_speed = speed_ctrl.value
            choice = input('+ for increasing position, - for decreasing position').strip()
            while choice not in '+-':
                choice = input('+ for increasing position, - for decreasing position').strip()
            if choice == '+':
                interface.set_actuator_dir('forward')
            elif choice == '-':
                interface.set_actuator_dir('backward')
            choice = input('+ for increasing speed, - for decreasing speed').strip()
            while choice not in '+-':
                choice = input('+ for increasing speed, - for decreasing speed').strip()
            if choice == '+':
                tmp = speed_ctrl.value + 10
                if tmp > (2 ** speed_ctrl.bits):
                    speed_ctrl.set_level(2 ** speed_ctrl.bits)
                else:
                    speed_ctrl.set_level(tmp)
            elif choice == '-':
                tmp = speed_ctrl.value - 10
                if tmp < 0:
                    speed_ctrl.set_level(0)
                else:
                    speed_ctrl.set_level(tmp)
            input('Hit enter/return to stop')
            done = input('done? (y/n)').strip()
        return 'success'
    except KeyboardInterrupt:
        speed_ctrl.set_level(speed_ctrl.stop)
        return 'terminated'
