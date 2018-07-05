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
from random import randrange, choice

from libs.sparkfun_openscale import OpenScale


class TestOpenScale(TestCase):

    def test_load_config_from_device(self):
        self.fail()

    def test_parse_menu_response(self):
        baudrate = choice(OpenScale.BAUDRATES)
        tare = randrange(-2 ** 31, 2 ** 31 - 1)
        cal = randrange(-2 ** 31, 2 ** 31 - 1)
        report_rate = randrange(0, 2 ** 16 - 1)
        decimal_places = randrange(0, 12)
        avgs = randrange(1, 10)
        timestamp = choice(('On', 'Off'))
        units = choice(('kg', 'lbs'))
        local = choice(('On', 'Off'))
        remote = choice(('On', 'Off'))
        led = choice(('Blink', 'Off'))
        trigger = choice(('On', 'Off'))
        raw = choice(('On', 'Off'))
        trigger_char = randrange(33, 126)
        dummy_res = '1) Tare scale to zero [{}]\r\n' \
                    '2) Calibrate scale [{}]\r\n' \
                    '3) Timestamp [{}]\r\n' \
                    '4) Set report rate [{}]\r\n' \
                    '5) Set baud rate [{} bps]\r\n' \
                    '6) Change units of measure [{}]\r\n' \
                    '7) Decimals [{}]\r\n' \
                    '8) Average amount [{}]\r\n' \
                    '9) Local temp [{}]\r\n' \
                    'r) Remote temp [{}]\r\n' \
                    's) Status LED [{}]\r\n' \
                    't) Serial trigger [{}]\r\n' \
                    'q) Raw reading [{}]\r\n' \
                    'c) Trigger character: [{}]\r\n' \
                    'x) Exit\r\n' \
                    '>'.format(tare, cal, timestamp, report_rate, baudrate, units,
                               decimal_places, avgs, local, remote, led, trigger,
                               raw, trigger_char).encode('utf-8')
        timestamp = False if timestamp == 'Off' else True
        local = False if local == 'Off' else True
        remote = False if remote == 'Off' else True
        led = False if led == 'Off' else True
        trigger = False if trigger == 'Off' else True
        raw = False if raw == 'Off' else True
        trigger_char = chr(trigger_char).encode('utf-8')

        # todo: figure out better method than a monkey patch
        def open(cls):
            cls.is_open = True

        OpenScale._reconfigure_port = lambda arg: True
        OpenScale.read_until = lambda self, terminator: dummy_res
        OpenScale.open = open
        OpenScale.reset_input_buffer = lambda *args: True
        OpenScale.write = lambda *args: True
        OpenScale.flush = lambda *args: True
        scale = OpenScale()
        scale.is_open = True
        res = scale.parse_menu_response()
        self.assertEqual(res['baud'], baudrate, 'Baudrate parsing failed')
        self.assertEqual(res['tare'], tare, 'Tare parsing failed')
        self.assertEqual(res['calibrate'], cal, 'Calibrate parsing failed')
        self.assertEqual(res['report_rate'], report_rate, 'Report rate parsing failed')
        self.assertEqual(res['decimal_places'], decimal_places, 'Decimal places parsing failed')
        self.assertEqual(res['num_avg'], avgs, 'Average amount parsing failed')
        self.assertEqual(res['timestamp'], timestamp, 'Timestamp parsing failed')
        self.assertEqual(res['units'], units, 'Units parsing failed')
        self.assertEqual(res['local_temp_enable'], local, 'local temperature enable parsing failed')
        self.assertEqual(res['remote_temp_enable'], remote, 'remote temperature enable parsing failed')
        self.assertEqual(res['status_led'], led, 'LED status parsing failed')
        self.assertEqual(res['serial_trigger_enable'], trigger, 'trigger enable status parsing failed')
        self.assertEqual(res['raw_reading'], raw, 'raw read enable status parsing failed')
        self.assertEqual(res['trigger_char'], trigger_char, 'trigger char parsing failed')

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
