#! /usr/bin/env python
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
pi_control
actuator.py
Author: Danyal Ahsanullah
Date: 7/25/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: 
"""
from typing import Tuple, Union
from numbers import Real as _Real
from collections import deque as _deque

from libs.utils import GPIO
from libs.utils import in2mm
from libs.hal.constants import GLOBAL_VCC, PINS, LOCK
# noinspection PyPep8Naming
from libs.hal.adc import ADS1115Interface as A2D
# noinspection PyPep8Naming
from libs.hal.dac import MCP4725Interface as D2A
from libs.data_router import add_to_poll, publish
from libs.hal.sparkfun_openscale import OpenScale as LoadCell


class Actuator:
    """
    Actuator interface for main drive arm
    """
    stroke = 12  # stroke length (inches)
    pot_value = 10000  # 10k pot
    pot_voltage = GLOBAL_VCC  # connected to a 3v3 supply rail
    inches_per_second = {35: {'none': 2.00, 'full': 1.38},
                         50: {'none': 1.14, 'full': 0.83},
                         150: {'none': 0.37, 'full': 0.28},
                         }  # key is force (lbs)
    distance_per_volt = stroke / pot_voltage

    # size for inbuilt moving average filter
    kernel_size = 5

    def __init__(self, position_sensor: A2D, speed_controller: D2A, force_sensor: LoadCell,
                 pos_limits: dict = None, units: str = 'raw', movement_controller=None):
        """
        create an actuator interface
        :param position_sensor: ADC handle for position
        :param speed_controller: DAC handle for speed control
        :param force_sensor: ADC handle for measuring applied force
        :param pos_limits: dictionary of {'high':<int>, 'low':<int>} that enforce limits on positions
        :param units:
        """
        self.convert_units = {
            'raw': lambda level: level,
            'in': lambda level: level * self.distance_per_level,
            'mm': lambda level: in2mm(level * self.distance_per_level),
        }
        self.tolerance = 5
        self.position_sensor = position_sensor
        self.speed_controller = speed_controller
        self.force_sensor = force_sensor
        self.distance_per_level = self.distance_per_volt * self.position_sensor.step_size
        self.pos_limit_low = 5000
        self.pos_limit_high = 26000
        self.units = units
        self.direction = 'forward'
        if pos_limits is not None:
            self.pos_limit_low = pos_limits.pop('low', self.pos_limit_low)
            self.pos_limit_high = pos_limits.pop('high', self.pos_limit_high)
        if movement_controller is not None:
            self.movement_controller = movement_controller
        add_to_poll(self._get_pos)
        add_to_poll(self._get_speed)
        add_to_poll(self._get_load)

    def _get_pos(self):
        return self.position

    def _get_speed(self):
        return self.speed

    def _get_load(self):
        return self.load

    # todo: implement this
    def mount_controller(self, controller):
        pass

    @property
    @publish('actuator.position', ('pos_info',))
    def position(self) -> _Real:
        """
        gets position as the units value
        :return: position in appropriate units
        """
        # LOCK.acquire()
        pos = self.position_sensor.read_single()
        while pos < 1000:
            pos = self.position_sensor.read_single()
        return self.convert_units[self.units](pos)
        # LOCK.release()

    @property
    @publish('actuator.force', ('force', 'local_temp', 'timestamp'))
    def load(self) -> Tuple[float, float, int]:
        load = self.force_sensor.get_reading()
        return load

    @property
    @publish('actuator.speed', ('speed',))
    def speed(self):
        return self.speed_controller.value

    @speed.setter
    def speed(self, value):
        self.speed_controller.set_level(value)

    def set_actuator_dir(self, direction: Union[str, None] = None) -> None:
        """
        sets actuator direction as forward or backward. If direction is not passed, the current direction is flipped.
        :type direction: str or None
        :param direction: string describing direction. Either '(f)orward' or '(b)ackward'
        :return: None
        """
        if direction is None:
            GPIO.output(PINS['relay_1'], not GPIO.input(PINS['relay_1']))
            self.direction = 'forward' if self.direction != 'forward' else 'backward'
        if direction in {'forward', 'f'}:
            GPIO.output(PINS['relay_1'], GPIO.HIGH)
            self.direction = 'forward'
        elif direction in {'backward', 'b'}:
            GPIO.output(PINS['relay_1'], GPIO.LOW)
            self.direction = 'backward'
        else:
            raise ValueError('unknown direction {!r}'.format(direction))

    # will require speed vs voltage information
    # todo: get data for speed vs voltage info
    # https://github.com/an-oreo/pi_control/issues/9
    def set_out_speed(self, speed: Union[int, float]) -> None:
        self.speed_controller.set_level(speed)
        return None
        # raise NotImplementedError('no information known for this')

    def set_position(self, position: Union[int, float], speed: Union[float, int, None] = None) -> None:
        """
        sets actuator to provided position. if overshoot is detected, attempts to correct.
        :param position: position value like those obtained from self.position
        :param speed: speed value to be used for movement. If not supplied, will use speed_controller default speed.
        :return: None
        """
        flag = False
        if speed is None:
            speed = self.speed_controller.default_val
        eps = self.tolerance
        # value = self.position_sensor.read_single()
        positions = _deque(maxlen=self.kernel_size)
        # fill in the queue for values
        while len(positions) < self.kernel_size:
            pos = self.position
            if pos > 100:
                positions.append(pos)
        value = sum(positions) / len(positions)
        # print(value)
        if abs(value - position) < eps:
            self.speed_controller.set_level(0)
            # print(f'target achieved\ndesired: {position}\nachieved: {value}\nerror: {position - value}')
            return None
        if value >= position:
            self.set_actuator_dir('backward')
        else:  # value < position
            self.set_actuator_dir('forward')
        self.speed_controller.set_level(speed)
        while True:
            while not flag:
                pos = self.position
                # print(pos)
                if pos > 100:
                    positions.append(pos)
                    flag = True
            flag = False
            # pos = self.position
            # positions.append(pos)
            value = sum(positions) / positions.maxlen
            # print(self.speed_controller.value, value)
            if abs(value - position) < eps:
                self.speed_controller.set_level(0)
                # print(f'target achieved\ndesired: {position}\nachieved: {value}\nerror: {position - value}')
                # self.position_sensor.stop_adc()
                return None
            elif value > position and self.direction != 'backward':  # too far, go back
                print(value)
                print('back')
                self.set_actuator_dir('backward')
            elif value < position and self.direction != 'forward':  # not far enough, go forward
                print(value)
                print('forward')
                self.set_actuator_dir('forward')

    def level2position(self, level: int, units: str = 'in') -> float:
        """
        converts a integer level to a position value
        :param level: integer level like one obtained form self.position
        :param units: str
        :return: float of newly converted units
        """
        pos = level * self.distance_per_level  # returns in inches
        if units == 'mm':
            return in2mm(pos)
        else:
            return pos

    def reset_max(self):
        self.set_position(self.pos_limit_high)

    def reset_min(self):
        self.set_position(self.pos_limit_low)
