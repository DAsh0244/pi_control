#! /usr/bin/env python
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
pi_control
test_open_scale.py
Author: Danyal Ahsanullah
Date: 7/3/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: 
"""
from unittest import TestCase
from random import randrange, uniform, choice

from libs.sparkfun_openscale import OpenScale


class TestOpenScale(TestCase):

    def test_session(self):
        self.fail()

    def test_load_config_from_device(self):
        self.fail()

    def test_parse_menu_response(self):
        scale = OpenScale()
        tare = randrange(-2 ** 31, 2 ** 31 - 1)
        cal = randrange(-2 ** 31, 2 ** 31 - 1)
        timestamp = choice(('On', 'Off'))
        report_rate = randrange(0, 2 ** 16 - 1)
        baudrate = choice(scale.BAUDRATES)
        units = choice(('kg', 'lbs'))
        decimal_places = randrange(0, 12)
        avgs = randrange(1, 10)
        local = choice(('On', 'Off'))
        remote = choice(('On', 'Off'))
        led = choice(('Blink', 'Off'))
        trigger = choice(('On', 'Off'))
        raw = choice(('On', 'Off'))
        trigger_char = chr(randrange(33, 126)).encode('urf-8')
        dummy_res = '1) Tare scale to zero {}\r\n' \
                    '2) Calibrate scale {}\r\n' \
                    '3) Timestamp {}\r\n' \
                    '4) Set report rate {}\r\n' \
                    '5) Set baud rate {} bps\r\n' \
                    '6) Change units of measure {}\r\n' \
                    '7) Decimals {}\r\n' \
                    '8) Average amount {}\r\n' \
                    '9) Local temp {}\r\n' \
                    'r) Remote temp {}\r\n' \
                    's) Status LED {}\r\n' \
                    't) Serial trigger {}\r\n' \
                    'q) Raw reading {}\r\n' \
                    'c) Trigger character: {}\r\n' \
                    'x) Exit\r\n' \
                    '>'.format(tare, cal, timestamp, report_rate, baudrate, units,
                               decimal_places, avgs, local, remote, led, trigger,
                               raw, trigger_char)

    def test_triggered_read(self):
        self.fail()

    def test_timestamp_enable(self):
        self.fail()

    def test_report_rate(self):
        self.fail()

    def test_calibrate(self):
        self.fail()

    def test_trigger_char(self):
        self.fail()

    def test_local_temp_enable(self):
        self.fail()

    def test_remote_temp_enable(self):
        self.fail()

    def test_units(self):
        self.fail()

    def test_decimals(self):
        self.fail()

    def test_num_avgs(self):
        self.fail()

    def test_status_led(self):
        self.fail()

    def test_raw_reading_enable(self):
        self.fail()

    def test_serial_trigger_enable(self):
        self.fail()

    def test_tare(self):
        self.fail()

    def test_read_cal_info(self):
        self.fail()

    def test_get_reading(self):
        self.fail()


if __name__ == '__main__':
    import unittest

    unittest.main()
