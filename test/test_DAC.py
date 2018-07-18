#! /usr/bin/env python
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
pi_control
test_MCP4725.py
Author: Danyal Ahsanullah
Date: 7/11/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: 
"""
from copy import deepcopy
from random import randrange, uniform, choice
from unittest import TestCase
from libs.hal import _MCP4725 as DAC


class TestDAC(TestCase):
    def test_set_level(self):
        dac = DAC()
        new_level = randrange(0, dac.levels)
        old_history = deepcopy(dac.value_history)
        dac.set_level(new_level)
        self.assertEqual(new_level, dac.value_history[-1], 'new value not appended to history')
        self.assertNotEqual(old_history, dac.value_history, 'history not changed!')

    def test_set_voltage(self):
        supply = choice((3.3, 5))
        dac = DAC(vcc=supply)
        new_voltage = uniform(0, supply)
        equal_level = round(new_voltage * supply / (1 << dac.bits))
        old_history = deepcopy(dac.value_history)
        dac.set_voltage(new_voltage)
        self.assertEqual(equal_level, dac.value_history[-1], 'new value not appended to history')
        self.assertNotEqual(old_history, dac.value_history, 'history not changed!')

    def test_level2voltage(self):
        dac = DAC()
        new_level = randrange(0, dac.levels)
        equal_voltage = new_level * dac.vcc / (1 << dac.bits)
        self.assertAlmostEqual(equal_voltage, dac.level2voltage(new_level), 6, 'voltage mismatch!')

    def test_voltage2level(self):
        supply = choice((3.3, 5))
        dac = DAC(vcc=supply)
        new_voltage = uniform(0, supply)
        equal_level = round(new_voltage * supply / (1 << dac.bits))
        self.assertEqual(equal_level, dac.voltage2level(new_voltage), 'voltage mismatch!')
