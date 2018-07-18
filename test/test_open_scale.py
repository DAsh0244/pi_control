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
from random import randrange, choice, uniform

from libs.sparkfun_openscale import OpenScale


class TestOpenScale(TestCase):
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
                '>'  # .format(
    #            randrange(-2 ** 31, 2 ** 31 - 1),  # tare
    #            randrange(-2 ** 31, 2 ** 31 - 1),  # cal
    #            randrange(0, 2 ** 16 - 1),  # timestamp
    #            randrange(450, 1000),  # report rate
    #            choice(OpenScale.BAUDRATES),  # baud
    #            choice(('kg', 'lbs')),  # units
    #            randrange(1, 10),  # decimal places
    #            randrange(1, 10),  # averages
    #            choice(('On', 'Off')),  # local temp
    #            choice(('On', 'Off')),  # remote temp
    #            choice(('Blink', 'Off')),  # status led
    #            choice(('On', 'Off')),  # trigger enable
    #            choice(('On', 'Off')),  # raw read enable
    #            randrange(33, 126)  # trigger char
    #            )

    def monkey_patch_serial(self):
        def open(cls):
            cls.is_open = True

        OpenScale._reconfigure_port = lambda arg: True
        OpenScale.read_until = lambda s, terminator: self.dummy_res
        OpenScale.open = open
        OpenScale.reset_input_buffer = lambda *args: True
        OpenScale.write = lambda *args: True
        OpenScale.flush = lambda *args: True

    def gen_fake_menu(self, monkey_patch: bool = True):
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
        self.dummy_res = self.dummy_res.format(tare, cal, timestamp, report_rate, baudrate, units,
                                               decimal_places, avgs, local, remote, led, trigger,
                                               raw, trigger_char).encode('utf-8')
        timestamp = False if timestamp == 'Off' else True
        local = False if local == 'Off' else True
        remote = False if remote == 'Off' else True
        led = False if led == 'Off' else True
        trigger = False if trigger == 'Off' else True
        raw = False if raw == 'Off' else True
        trigger_char = chr(trigger_char).encode('utf-8')

        if monkey_patch:
            self.monkey_patch_serial()
            scale = OpenScale()
            scale.is_open = True
        else:
            scale = OpenScale()
        return avgs, baudrate, cal, decimal_places, led, local, raw, remote, \
               report_rate, scale, tare, timestamp, trigger, trigger_char, units

    # def setUp(self):
    #     self.avgs, self.baudrate, self.cal, self.decimal_places, \
    #     self.led, self.local, self.raw, self.remote, self.report_rate, \
    #     self.scale, self.tare, self.timestamp, self.trigger, self.trigger_char, self.units = self.gen_fake_menu()

    def test_load_config_from_device(self):
        avgs, baudrate, cal, decimal_places, led, local, raw, remote, report_rate, \
        scale, tare, timestamp, trigger, trigger_char, units = self.gen_fake_menu()
        scale.load_config_from_device()
        self.assertEqual(scale.baudrate, baudrate, 'Baudrate parsing failed')
        self.assertEqual(scale.tare, tare, 'Tare parsing failed')
        self.assertEqual(scale.calibrate, cal, 'Calibrate parsing failed')
        self.assertEqual(scale.report_rate, report_rate, 'Report rate parsing failed')
        self.assertEqual(scale.decimals, decimal_places, 'Decimal places parsing failed')
        self.assertEqual(scale.num_avgs, avgs, 'Average amount parsing failed')
        self.assertEqual(scale.timestamp_enable, timestamp, 'Timestamp parsing failed')
        self.assertEqual(scale.units, units, 'Units parsing failed')
        self.assertEqual(scale.local_temp_enable, local, 'local temperature enable parsing failed')
        self.assertEqual(scale.remote_temp_enable, remote, 'remote temperature enable parsing failed')
        self.assertEqual(scale.status_led, led, 'LED status parsing failed')
        self.assertEqual(scale.raw_reading_enable, raw, 'raw read enable status parsing failed')
        self.assertEqual(scale.serial_trigger_enable, trigger, 'trigger enable status parsing failed')
        self.assertEqual(scale.trigger_char, trigger_char, 'trigger char parsing failed')

    def test_parse_menu_response(self):
        avgs, baudrate, cal, decimal_places, led, local, raw, remote, report_rate, \
        scale, tare, timestamp, trigger, trigger_char, units = self.gen_fake_menu()
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

    # todo implement testing for getters/setters
    def test_trigger_char(self):
        avgs, baudrate, cal, decimal_places, led, local, raw, remote, report_rate, \
        scale, tare, timestamp, trigger, trigger_char, units = self.gen_fake_menu()
        self.assertEqual(scale.trigger_char, trigger_char, 'baseline: trigger char mismatch')
        tmp_chr = chr(randrange(33, 126))
        while trigger_char == tmp_chr:
            tmp_chr = chr(randrange(33, 126))
        scale.trigger_char = tmp_chr
        trigger_char = tmp_chr.encode('utf-8')
        self.assertEqual(scale.trigger_char, trigger_char, 'modified trigger_char: trigger char mismatch')

    def test_serial_trigger_enable(self):
        avgs, baudrate, cal, decimal_places, led, local, raw, remote, report_rate, \
        scale, tare, timestamp, trigger, trigger_char, units = self.gen_fake_menu()
        self.assertEqual(scale.serial_trigger_enable, trigger, 'baseline: trigger enable mismatch')
        scale.serial_trigger_enable = trigger = not scale.serial_trigger_enable
        self.assertEqual(scale.serial_trigger_enable, trigger,
                         'modified trigger_enable: trigger enable status mismatch')

    def test_timestamp_enable(self):
        avgs, baudrate, cal, decimal_places, led, local, raw, remote, report_rate, \
        scale, tare, timestamp, trigger, trigger_char, units = self.gen_fake_menu()
        self.assertEqual(scale.timestamp_enable, timestamp, 'baseline: timestamp enable mismatch')
        scale.timestamp_enable = timestamp = not scale.timestamp_enable
        self.assertEqual(scale.timestamp_enable, timestamp,
                         'modified timestamp enable: timestamp enable status mismatch')

    def test_local_temp_enable(self):
        avgs, baudrate, cal, decimal_places, led, local, raw, remote, report_rate, \
        scale, tare, timestamp, trigger, trigger_char, units = self.gen_fake_menu()
        self.assertEqual(scale.local_temp_enable, local, 'baseline: local temp enable mismatch')
        scale.local_temp_enable = local = not scale.local_temp_enable
        self.assertEqual(scale.local_temp_enable, local,
                         'modified local temp enable: local temp enable status mismatch')

    def test_remote_temp_enable(self):
        avgs, baudrate, cal, decimal_places, led, local, raw, remote, report_rate, \
        scale, tare, timestamp, trigger, trigger_char, units = self.gen_fake_menu()
        self.assertEqual(scale.remote_temp_enable, remote, 'baseline: remote temp enable mismatch')
        scale.remote_temp_enable = remote = not scale.remote_temp_enable
        self.assertEqual(scale.remote_temp_enable, remote,
                         'modified remote temp enable: remote temp enable status mismatch')

    def test_status_led(self):
        avgs, baudrate, cal, decimal_places, led, local, raw, remote, report_rate, \
        scale, tare, timestamp, trigger, trigger_char, units = self.gen_fake_menu()
        self.assertEqual(scale.status_led, led, 'baseline: led enable mismatch')
        scale.status_led = led = not scale.status_led
        self.assertEqual(scale.status_led, led, 'modified led enable: led enable status mismatch')

    def test_raw_reading_enable(self):
        avgs, baudrate, cal, decimal_places, led, local, raw, remote, report_rate, \
        scale, tare, timestamp, trigger, trigger_char, units = self.gen_fake_menu()
        self.assertEqual(scale.raw_reading_enable, raw, 'baseline: raw read enable mismatch')
        scale.raw_reading_enable = raw = not scale.raw_reading_enable
        self.assertEqual(scale.raw_reading_enable, raw, 'modified raw read enable: raw read enable status mismatch')

    def test_units(self):
        avgs, baudrate, cal, decimal_places, led, local, raw, remote, report_rate, \
        scale, tare, timestamp, trigger, trigger_char, units = self.gen_fake_menu()
        self.assertEqual(scale.units, units, 'baseline: units do not match')
        scale.units = units = choice(('lbs', 'kg'))
        self.assertEqual(scale.units, units, 'modified: units do not match')

    def test_report_rate(self):
        avgs, baudrate, cal, decimal_places, led, local, raw, remote, report_rate, \
        scale, tare, timestamp, trigger, trigger_char, units = self.gen_fake_menu()
        self.assertEqual(scale.report_rate, report_rate, 'baseline: report rate mismatch')
        scale.report_rate = report_rate = randrange(500, 1000)
        self.assertEqual(scale.report_rate, report_rate, 'modified: report rate mismatch')

    def test_calibrate(self):
        avgs, baudrate, cal, decimal_places, led, local, raw, remote, report_rate, \
        scale, tare, timestamp, trigger, trigger_char, units = self.gen_fake_menu()
        self.assertEqual(scale.calibrate, cal, 'baseline: calibrate val mismatch')
        if cal > (2 ** 31 - 1) / 2:
            cal -= randrange(1, 180000)
        else:
            cal += randrange(1, 180000)
        scale.calibrate = cal
        self.assertEqual(scale.calibrate, cal, 'modified: calibrate val mismatch')

    def test_decimals(self):
        avgs, baudrate, cal, decimal_places, led, local, raw, remote, report_rate, \
        scale, tare, timestamp, trigger, trigger_char, units = self.gen_fake_menu()
        self.assertEqual(scale.decimals, decimal_places, 'baseline: decimal place mismatch')
        scale.decimals = decimal_places = randrange(1, 10)
        self.assertEqual(scale.decimals, decimal_places, 'modified: decimal place mismatch')

    def test_num_avgs(self):
        avgs, baudrate, cal, decimal_places, led, local, raw, remote, report_rate, \
        scale, tare, timestamp, trigger, trigger_char, units = self.gen_fake_menu()
        self.assertEqual(scale.num_avgs, avgs, 'baseline: num avgs mismatch')
        scale.num_avgs = avgs = randrange(1, 10)
        self.assertEqual(scale.num_avgs, avgs, 'modified: num avgs mismatch')

    def test_tare_device(self):
        t1, t2 = randrange(-1234567, 1234567), randrange(-1234567, 1234567)
        OpenScale._response = 'Tare point 1: {}\r\n' \
                              'Tare point 2: {}\r\n'.format(t1, t2)

        def read_until(self, terminator=b'\n'):
            # global response
            idx = self._response.index(str(terminator, 'utf-8'))
            buf = self._response[:idx + len(terminator)]
            self._response = self._response[idx + len(terminator):]
            return bytes(buf, 'utf-8')

        avgs, baudrate, cal, decimal_places, led, local, raw, remote, report_rate, \
        scale, tare, timestamp, trigger, trigger_char, units = self.gen_fake_menu()
        OpenScale.read_until = read_until
        r1, r2 = scale.tare_device()
        self.assertEqual(t1, r1, 'tare point 1 mismatch')
        self.assertEqual(t2, r2, 'tare point 2 mismatch')

    def test_read_cal_info(self):
        avgs, baudrate, cal, decimal_places, led, local, raw, remote, report_rate, \
        scale, tare, timestamp, trigger, trigger_char, units = self.gen_fake_menu()
        reading = uniform(-1000.0, 1000.0)
        OpenScale.read = lambda self, num_bytes: None
        OpenScale.read_until = lambda self, terminator: 'Reading: [{} {}] Calibration Factor: {}' \
                                                        '\r\n'.format(reading, units, cal).encode('utf-8')
        cal_info = {'reading': reading,
                    'units': units,
                    'cal_factor': cal,
                    }
        self.assertEqual(scale.read_cal_info(), cal_info, 'cal info mismatch')

    def test_get_reading(self):
        avgs, baudrate, cal, decimal_places, led, local, raw, remote, report_rate, \
        scale, tare, timestamp, trigger, trigger_char, units = self.gen_fake_menu()

        reading = uniform(-1000.0, 1000.0)
        raw_read = randrange(-10000, 10000)  # todo: set this to map to reading
        remote_tmp = uniform(-1000.0, 1000.0)
        local_tmp = uniform(-1000.0, 1000.0)
        timestamp_val = randrange(0, 2 ** 32 - 1)

        send_map = {
            # order: ret     (timestamp,  cal_read, unit, raw, local, remote)
            0b01000: '{} {}\r\n'.format(reading, units).encode('utf-8'),
            0b01001: '{} {},{}\r\n'.format(reading, units, remote_tmp).encode('utf-8'),
            0b01010: '{} {},{}\r\n'.format(reading, units, local_tmp).encode('utf-8'),
            0b01011: '{} {},{},{}\r\n'.format(reading, units, local_tmp, remote_tmp).encode('utf-8'),
            0b01100: '{} {},{}\r\n'.format(reading, units, raw_read).encode('utf-8'),
            0b01101: '{} {},{},{}\r\n'.format(reading, units, raw_read, remote_tmp).encode('utf-8'),
            0b01110: '{} {},{},{}\r\n'.format(reading, units, raw_read, local_tmp).encode('utf-8'),
            0b01111: '{} {},{},{},{}\r\n'.format(reading, units, raw_read, local_tmp, remote_tmp).encode('utf-8'),
            0b11000: '{},{} {}\r\n'.format(timestamp_val, reading, units).encode('utf-8'),
            0b11001: '{},{} {},{}\r\n'.format(timestamp_val, reading, units, remote_tmp).encode('utf-8'),
            0b11010: '{},{} {},{}\r\n'.format(timestamp_val, reading, units, local_tmp).encode('utf-8'),
            0b11011: '{},{} {},{},{}\r\n'.format(timestamp_val, reading, units, local_tmp, remote_tmp).encode('utf-8'),
            0b11100: '{},{} {},{}\r\n'.format(timestamp_val, reading, units, raw_read).encode('utf-8'),
            0b11101: '{},{} {},{},{}\r\n'.format(timestamp_val, reading, units, raw_read, remote_tmp).encode('utf-8'),
            0b11110: '{},{} {},{},{}\r\n'.format(timestamp_val, reading, units, raw_read, local_tmp).encode('utf-8'),
            0b11111: '{},{} {},{},{},{}\r\n'.format(timestamp_val, reading, units, raw_read, local_tmp,
                                                    remote_tmp).encode('utf-8'),
        }

        ret_map = {
            # order: (timestamp, cal_read, unit, raw, local, remote)
            0b01000: (None, reading, units, None, None, None),
            0b01001: (None, reading, units, None, None, remote_tmp),
            0b01010: (None, reading, units, None, local_tmp, None),
            0b01011: (None, reading, units, None, local_tmp, remote_tmp),
            0b01100: (None, reading, units, raw_read, None, None),
            0b01101: (None, reading, units, raw_read, None, remote_tmp),
            0b01110: (None, reading, units, raw_read, local_tmp, None),
            0b01111: (None, reading, units, raw_read, local_tmp, remote_tmp),
            0b11000: (timestamp_val, reading, units, None, None, None),
            0b11001: (timestamp_val, reading, units, None, None, remote_tmp),
            0b11010: (timestamp_val, reading, units, None, local_tmp, None),
            0b11011: (timestamp_val, reading, units, None, local_tmp, remote_tmp),
            0b11100: (timestamp_val, reading, units, raw_read, None, None),
            0b11101: (timestamp_val, reading, units, raw_read, None, remote_tmp),
            0b11110: (timestamp_val, reading, units, raw_read, local_tmp, None),
            0b11111: (timestamp_val, reading, units, raw_read, local_tmp, remote_tmp),
        }

        key = (scale._timestamp_enable << 4) | \
              0b01000 | \
              (scale._raw_reading_enable << 2) | \
              (scale._local_temp_enable << 1) | \
              scale._remote_temp_enable

        OpenScale.read_until = lambda self, terminator: send_map[key]

        self.assertEqual(scale.get_reading(), ret_map[key], 'reading incorrectly parsed')

    def test_triggered_read(self):
        wrote_chr = None
        avgs, baudrate, cal, decimal_places, led, local, raw, remote, report_rate, \
        scale, tare, timestamp, trigger, trigger_char, units = self.gen_fake_menu()

        def write(self, data):
            nonlocal wrote_chr
            wrote_chr = data

        OpenScale.write = write
        scale.triggered_read()
        self.assertEqual(wrote_chr, trigger_char, 'mismatch of triggered read char')

    def test_to_force(self):
        avgs, baudrate, cal, decimal_places, led, local, raw, remote, report_rate, \
        scale, tare, timestamp, trigger, trigger_char, units = self.gen_fake_menu()

        reading = uniform(-1000.0, 1000.0)

        self.assertAlmostEqual(scale.to_force(reading, units),
                               reading * (9.80665 if units == 'kg' else 32.174049),
                               'conversion failed!')


if __name__ == '__main__':
    import unittest

    unittest.main()
