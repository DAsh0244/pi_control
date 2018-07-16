#! /usr/bin/env python
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
pi_control
test_actuator.py
Author: Danyal Ahsanullah
Date: 7/12/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: 
"""
from unittest import TestCase, main
from libs.hal import adc, dac, load_cell, actuator
import serial


class TestActuator(TestCase):

    def setup(self):
        self.serial_listener = serial.Serial('COM13')
        res = b'1) Tare scale to zero [345678]\r\n' \
              b'2) Calibrate scale [12345678]\r\n' \
              b'3) Timestamp [On]\r\n' \
              b'4) Set report rate [600]\r\n' \
              b'5) Set baud rate [9600 bps]\r\n' \
              b'6) Change units of measure [kg]\r\n' \
              b'7) Decimals [4]\r\n' \
              b'8) Average amount [2]\r\n' \
              b'9) Local temp [Off]\r\n' \
              b'r) Remote temp [On]\r\n' \
              b's) Status LED [Blink]\r\n' \
              b't) Serial trigger [Off]\r\n' \
              b'q) Raw reading [On]\r\n' \
              b'c) Trigger character: [48]\r\n' \
              b'x) Exit\r\n' \
              b'>'
        self.serial_listener.write(res)

    def test_components(self):
        self.assertIs(adc, actuator.position_sensor, 'actuator position sensor not adc!')
        self.assertIs(dac, actuator.speed_controller, 'actuator speed controller not dacc!')
        self.assertIs(load_cell, actuator.force_sensor, 'actuator force sensor not expected load cell!')

    # def test_position(self):
    #     self.fail()
    #
    # def test_level2position(self):
    #     self.fail()
    #
    # def test_load(self):
    #     self.fail()
    #
    # def test_set_actuator_dir(self):
    #     self.assertRaises(actuator.set_actuator_dir('q'), ValueError, 'actuator direction accepts bad input')
    #
    #
    # def test_set_out_speed(self):
    #     self.fail()
    #
    # def test_set_position(self):
    #     self.fail()
    #
    # def test_reset_max(self):
    #     self.fail()
    #
    # def test_reset_min(self):
    #     self.fail()


if __name__ == '__main__':
    main()
