#! /usr/bin/env python
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
pi_control
test_A2D.py
Author: Danyal Ahsanullah
Date: 7/11/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description:
"""
from random import uniform, choice, randrange
from unittest import TestCase
from libs.hal import _ADS1115 as A2D
from copy import deepcopy


class Test_A2D(TestCase):
    def test_get_last_result(self):
        adc = A2D()
        old_history = deepcopy(adc.history)
        adc.get_last_result()
        self.assertNotEqual(adc.history, old_history, 'histories matching. Implied no read')

    def test_max_voltage(self):
        gain = choice(tuple(A2D.pga_map.keys()))
        supply = choice((3.3, 5.0))
        adc = A2D(gain=gain, vcc=supply)
        self.assertAlmostEqual(min(A2D.pga_map[gain], supply), adc.max_voltage, 6,
                               'max voltage not calculated correctly')

    # def test_start_conversions(self):
    #     self.fail()
    #
    # def test_wait_for_sample(self):
    #     self.fail()
    #
    # def test_read_single(self):
    #     self.fail()
    #
    # def test_stop(self):
    #     self.fail()

    def test_level2voltage(self):
        gain = choice(tuple(A2D.pga_map.keys()))
        supply = choice((3.3, 5.0))
        adc = A2D(gain=gain, vcc=supply)
        level = randrange(A2D.min_level, A2D.max_level)
        step_size = 2 * min(A2D.pga_map[gain], supply) / adc.levels
        self.assertAlmostEqual(adc.level2voltage(level), level * step_size, 6,
                               'failed to map level to voltage correctly')

    def test_voltage2level(self):
        gain = choice(tuple(A2D.pga_map.keys()))
        adc = A2D(gain=gain)
        voltage = uniform(-adc.max_voltage, adc.max_voltage)
        supply = choice((3.3, 5.0))
        step_size = 2 * min(A2D.pga_map[gain], supply) / adc.levels
        level = round(voltage / step_size)
        self.assertAlmostEqual(adc.voltage2level(voltage), level, 6, 'voltage backward mapping failed')
