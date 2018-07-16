#! /usr/bin/env python
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
pi_control
test_thermocouple.py
Author: Danyal Ahsanullah
Date: 7/12/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: 
"""
from unittest import TestCase
from libs.hal import Thermocouple
from random import choice


class TestThermocouple(TestCase):
    thermocouple_types = ('B', 'E', 'J', 'K', 'N', 'R', 'S', 'T')
    num_avgs = (1, 2, 4, 8, 16)

    def setUp(self):
        self.tc_type = choice(self.thermocouple_types)
        self.avgs = choice(self.num_avgs)
        self.thermocouple = Thermocouple(tc_type=self.tc_type, num_avgs=self.avgs,
                                         software_spi={"clk": 13, "cs": 5, "do": 19, "di": 26})

    # def test_read_temp(self):
    #     self.fail()
    #
    # def test_read_internal_temp(self):
    #     self.fail()
    #
    # def test_fault_register(self):
    #     self.fail()

    def test_thermocouple_type(self):
        for tc_typ in self.thermocouple_types:
            self.thermocouple.thermocouple_type = tc_typ
            self.assertEqual(tc_typ, self.thermocouple._tc_type_str, 'thermocouple type mismatch')

    def test_averaging_samples(self):
        for avgs in self.num_avgs:
            self.thermocouple.averaging_samples = avgs
            self.assertEqual(avgs, self.thermocouple._avg_samples, 'thermocouple type mismatch')

    def test_temperature_byte_conversions(self):

        """
        TAKEN FROM https://github.com/johnrbnsn/Adafruit_Python_MAX31856/blob/master/Adafruit_MAX31856/test_MAX31856.py
        Checks the byte conversion for various known temperature byte values.
        """

        # -------------------------------------------#
        # Test Thermocouple Temperature Conversions #
        byte2 = 0x01
        byte1 = 0x70
        byte0 = 0x20
        decimal_temp = self.thermocouple._thermocouple_temp_from_bytes(byte0, byte1,
                                                                       byte2)  # pylint: disable-msg=protected-access
        self.assertEqual(decimal_temp, 23.0078125)

        # Check a couple values from the datasheet
        byte2 = 0b00000001
        byte1 = 0b10010000
        byte0 = 0b00000000
        decimal_temp = self.thermocouple._thermocouple_temp_from_bytes(byte0, byte1,
                                                                       byte2)  # pylint: disable-msg=protected-access
        self.assertEqual(decimal_temp, 25.0)

        byte2 = 0b00000000
        byte1 = 0b00000000
        byte0 = 0b00000000
        decimal_temp = self.thermocouple._thermocouple_temp_from_bytes(byte0, byte1,
                                                                       byte2)  # pylint: disable-msg=protected-access
        self.assertEqual(decimal_temp, 0.0)

        byte2 = 0b11111111
        byte1 = 0b11110000
        byte0 = 0b00000000
        decimal_temp = self.thermocouple._thermocouple_temp_from_bytes(byte0, byte1,
                                                                       byte2)  # pylint: disable-msg=protected-access
        self.assertEqual(decimal_temp, -1.0)

        byte2 = 0b11110000
        byte1 = 0b01100000
        byte0 = 0b00000000
        decimal_temp = self.thermocouple._thermocouple_temp_from_bytes(byte0, byte1,
                                                                       byte2)  # pylint: disable-msg=protected-access
        self.assertEqual(decimal_temp, -250.0)

        # ---------------------------------#
        # Test CJ Temperature Conversions #
        msb = 0x1C
        lsb = 0x64
        decimal_cj_temp = self.thermocouple._cj_temp_from_bytes(msb, lsb)  # pylint: disable-msg=protected-access
        self.assertEqual(decimal_cj_temp, 28.390625)

        # Check a couple values from the datasheet
        msb = 0b01111111
        lsb = 0b11111100
        decimal_cj_temp = self.thermocouple._cj_temp_from_bytes(msb, lsb)  # pylint: disable-msg=protected-access
        self.assertEqual(decimal_cj_temp, 127.984375)

        msb = 0b00011001
        lsb = 0b00000000
        decimal_cj_temp = self.thermocouple._cj_temp_from_bytes(msb, lsb)  # pylint: disable-msg=protected-access
        self.assertEqual(decimal_cj_temp, 25)

        msb = 0b00000000
        lsb = 0b00000000
        decimal_cj_temp = self.thermocouple._cj_temp_from_bytes(msb, lsb)  # pylint: disable-msg=protected-access
        self.assertEqual(decimal_cj_temp, 0)

        msb = 0b11100111
        lsb = 0b00000000
        decimal_cj_temp = self.thermocouple._cj_temp_from_bytes(msb, lsb)  # pylint: disable-msg=protected-access
        self.assertEqual(decimal_cj_temp, -25)

        msb = 0b11001001
        lsb = 0b00000000
        decimal_cj_temp = self.thermocouple._cj_temp_from_bytes(msb, lsb)  # pylint: disable-msg=protected-access
        self.assertEqual(decimal_cj_temp, -55)
