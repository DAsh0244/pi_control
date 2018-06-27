#! /usr/bin/env python
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
import os

from libs.controller import PController, PDController, PIController, PIDController
from libs.utils import get_k_value, save_config

WAIT_TIMEOUT = 2


def calibrate_position(actuator_interface):
    """
    hand calibrate system position thresholds
    """
    speed_ctrl = actuator_interface.speed_controller
    pos_sense = actuator_interface.position_sensor
    print('Beginning calibration routine...')
    # TODO: figure out what relay 2 does
    actuator_interface.set_actuator_dir('forward')
    speed_ctrl.set_voltage(speed_ctrl.stop)
    print('Setting upper threshold')
    input('Hit enter/return to begin.')
    speed_ctrl.set_voltage(speed_ctrl.default_val)
    input('Hit enter/return to mark absolute upper threshold')
    actuator_interface.pos_limit_high = pos_sense.read_single()
    speed_ctrl.set_voltage(speed_ctrl.stop)
    print(actuator_interface.pos_limit_high)
    actuator_interface.set_actuator_dir('backward')  # prepare to go backwards
    print('Setting lower threshold')
    input('Hit enter/return to begin.')
    speed_ctrl.set_voltage(speed_ctrl.default_val)
    input('Hit enter/return to mark absolute lower threshold')
    actuator_interface.pos_limit_low = pos_sense.read_single()
    speed_ctrl.set_voltage(speed_ctrl.stop)
    print(actuator_interface.pos_limit_low)
    actuator_interface.set_actuator_dir('forward')
    print('Setting upper desired threshold')
    input('Hit enter/return  to begin.')
    speed_ctrl.set_voltage(speed_ctrl.default_val)
    input('Hit enter/return to mark desired upper threshold')
    actuator_interface.pos_threshold_high = pos_sense.read_single()
    speed_ctrl.set_voltage(speed_ctrl.stop)
    print(actuator_interface.pos_threshold_high)
    actuator_interface.set_actuator_dir('backward')  # prepare to go backwards
    print('Setting lower desired threshold')
    input('Hit enter/return  to begin.')
    speed_ctrl.set_voltage(speed_ctrl.default_val)
    input('Hit enter/return to mark desired lower threshold')
    actuator_interface.pos_threshold_low = pos_sense.read_single()
    speed_ctrl.set_voltage(speed_ctrl.stop)
    print(actuator_interface.pos_threshold_low)


def set_controller():
    control_map = {1: None, 2: PController, 3: PDController, 4: PIController, 5: PIDController}
    global CONTROLLER
    spaces = ' ' * 5
    valid_choices = set(map(str, control_map.keys()))
    print('set desired controller')
    print('valid choices:')
    print(spaces + '\n{}'.format(spaces).join(['{!s}: {!s}'.format(k, getattr(v, '__name__', v))
                                               for k, v in control_map.items()]))
    choice = input('Enter controller choice: ').strip()
    while choice not in valid_choices:  # delay int conversion to handle invalid string inputs
        choice = input('Enter controller choice: ').strip()
    controller = control_map[int(choice)]
    if controller is None:
        return
    coefficients = {k: 0.0 for k in controller.coefficients}
    for coefficient in controller.coefficients:
        coefficients[coefficient] = get_k_value(coefficient)
    CONTROLLER = controller(**coefficients)


def check_configurations(actuator_interface, controller):
    speed_ctrl = actuator_interface.speed_controller
    pos_sense = actuator_interface.position_sensor
    flag = False
    print('Testing current config of:')
    print('Controller: {!s}'.format(controller))
    print('Position Thresholds:')
    print('Absolute low: {}'.format(actuator_interface.pos_limit_low))
    print('Absolute high: {}'.format(actuator_interface.pos_limit_high))
    print('Set low: {}'.format(actuator_interface.pos_threshold_low))
    print('Set High: {}'.format(actuator_interface.pos_threshold_high))
    actuator_interface.set_actuator_dir('forward')
    speed_ctrl.set_level(1024)
    value = pos_sense.start_conversions()
    while not flag:
        if value >= actuator_interface.pos_limit_high:
            print('Hit absolute max limit', value)
            actuator_interface.set_actuator_dir('backward')
            flag = True
        pos_sense.wait_for_sample(timeout=WAIT_TIMEOUT)
        value = pos_sense.get_last_result()
    flag = False
    value = pos_sense.get_last_result()
    while not flag:
        if value <= actuator_interface.pos_limit_low:
            print('Hit absolute min limit', value)
            actuator_interface.set_actuator_dir('forward')
            flag = True
        pos_sense.wait_for_sample(timeout=WAIT_TIMEOUT)
        value = pos_sense.get_last_result()
    flag = False
    value = pos_sense.get_last_result()
    while not flag:
        if value >= actuator_interface.pos_threshold_high:
            print('Hit designated max limit', value)
            actuator_interface.set_actuator_dir('backward')
            flag = True
        pos_sense.wait_for_sample(timeout=WAIT_TIMEOUT)
        value = pos_sense.get_last_result()
    flag = False
    value = pos_sense.get_last_result()
    while not flag:
        if value <= actuator_interface.pos_threshold_low:
            speed_ctrl.set_voltage(speed_ctrl.stop)
            print('Hit designated min limit', value)
            actuator_interface.set_actuator_dir('forward')
            flag = True
        pos_sense.wait_for_sample(timeout=WAIT_TIMEOUT)
        value = pos_sense.get_last_result()
    speed_ctrl.set_level(speed_ctrl.stop)
    pos_sense.stop()


def calibrate(interface, params, nxt=None):
    # noinspection SpellCheckingInspection
    """
        calibrate actuator control
        allows for :
            thresholding:
                software implemented stroke boundaries
                safety and desired operating stroke definitions
            control method:
                P control - output speed is proportional to desired position to approach that position
                PD control - P control + output speed is modified by the rate of approach
                None - output speed is flat over entire duration
            testing and editing of generated parameters:
                test currently generated scheme
                editing any single point generated

        7 step process:
            1. define abs low (leave alone if limit switch)
            2. define abs high (leave alone if limit switch)
            3. define desired stroke low threshold
            4. define desired stroke high threshold
            5. define controller
            6. define desired actuator movement rates
            6.5. test current setup -- tweak values as wanted
            7. confirm cal data
        """
    # calibrate thresholds:
    if nxt is None:
        nxt = {'true': None}
    calibrate_position(interface)
    # set control scheme:
    set_controller()
    # test:
    check_configurations(interface, CONTROLLER)
    # reconfigure -- optional
    # edit = input('edit configuration? (y/n): ').strip().lower()
    # while edit not in ('y','n'):
    #     edit = input('edit configuration? (y/n): ').strip().lower()
    # if edit == 'y':
    #     edit_config()
    # confirm
    confirm = input('confirm settings? (y/n): ').strip().lower()
    while confirm not in ('y', 'n'):
        confirm = input('confirm settings? (y/n): ').strip().lower()
    if confirm == 'y':
        outfile = input('enter valid config file name: ').strip()
        while not os.access(os.path.dirname(outfile), os.W_OK):
            outfile = input('enter valid config file name: ').strip()
        save_config(outfile)
    return nxt['true']
