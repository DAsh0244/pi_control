#! /usr/bin/env python
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
pi_control
test_controller.py
Author: Danyal Ahsanullah
Date: 6/25/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: 
"""

# todo test cases!!!

# import random
from time import perf_counter
from unittest import TestCase
from src.libs import controller as control


class TestControllerBase(TestCase):
    def test_calc_correction(self):
        self.fail()

    def test_process(self):
        self.fail()


class TestPController(TestCase):
    def test_calc_correction(self):
        self.fail()


class TestPDController(TestCase):
    def test_calc_correction(self):
        self.fail()


class TestPIController(TestCase):
    def test_calc_correction(self):
        self.fail()


# noinspection PyUnreachableCode
class TestPIDController(TestCase):
    done = False
    target = 1
    err = 1e-5
    last_time = perf_counter()
    last_out = 0.0

    @staticmethod
    def get_input():
        return last_out

    @staticmethod
    def scale_output(outval):
        global last_out
        # last_out = outval * random.random()
        last_out = outval * 0.03

    def test_calc_correction(self):
        self.fail('must be implemented')
        ctrl = control.PIDController(10, 5, 0, input_func=get_input, output_func=scale_output)
        ctrl.ref = self.target
        print('time\tinput\tout\terr')
        start = perf_counter()
        while perf_counter() - start < 0.3:
            ctrl.process()
            print(ctrl.last_time, last_out, ctrl.out, ctrl.err, sep='\t')


if __name__ == '__main__':
    import unittest

    unittest.main()
