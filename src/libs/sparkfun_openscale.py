#! /usr/bin/env python
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
pi_control
sparkfun_openscale.py
Author: Danyal Ahsanullah
Date: 6/29/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: library for interfacing the Sparkfun OpenScale.
"""

import serial
from functools import wraps
from typing import Tuple, Dict, Union


# todo: get some form of config dumping and loading implemented


class OpenScale(serial.Serial):
    BAUD_MIN = 1200
    BAUD_MAX = 1000000
    # prompt for initial opening of config menu:
    #
    # b'1) Tare scale to zero [\d+]\r\n'\
    # b'2) Calibrate scale[\d+]\r\n'\
    # b'3) Timestamp [On|Off]\r\n'\
    # b'4) Set report rate [\d+]\r\n'\
    # b'5) Set baud rate [\d+ bps]\r\n'\
    # b'6) Change units of measure [lbs|kg]\r\n'\
    # b'7) Decimals [\d+]\r\n'\
    # b'8) Average amount [\d+]\r\n'\
    # b'9) Local temp [On|Off]\r\n'\
    # b'r) Remote temp [On|Off]\r\n'\
    # b's) Status LED [Blink|Off]\r\n'\
    # b't) Serial trigger [On|Off]\r\n'\
    # b'q) Raw reading [On|Off]\r\n'\
    # b'c) Trigger character: [\d+]\r\n'\
    # b'x) Exit'\r\n\
    # b'>'

    prompt_indexes = (
        ('tare', 23),
        ('calibrate', 19),
        ('timestamp', 14),
        ('report_rate', 20),
        ('baud', 18),
        ('units', 28),
        ('decimal_places', 13),
        ('num_avg', 19),
        ('local_temp_enable', 15),
        ('remote_temp_enable', 16),
        ('status_led', 15),
        ('serial_trigger_enable', 19),
        ('raw_reading', 16),
        ('trigger_char', 24),
    )

    def __init__(self, tare: int = 0, tare_val_1: int = 0, tare_val_2: int = 0, cal_value: int = 0,
                 timestamp_enable: bool = True, report_rate: int = 200, units: str = 'kg', decimal_places: int = 4,
                 num_avgs: int = 4, local_temp_enable: bool = False, remote_temp_enable: bool = False,
                 status_led: bool = True, serial_trigger_enable: bool = True, raw_reading_enable: bool = True,
                 trigger_char: bytes = b'0', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tare: int = tare
        self._tare_val_1: int = tare_val_1
        self._tare_val_2: int = tare_val_2
        self._cal_value: int = cal_value
        self._timestamp_enable: bool = timestamp_enable
        self._report_rate: int = report_rate
        self._units: str = units
        self._decimal_places: int = decimal_places
        self._num_avgs: int = num_avgs
        self._local_temp_enable: bool = local_temp_enable
        self._remote_temp_enable: bool = remote_temp_enable
        self._status_led: bool = status_led
        self._serial_trigger_enable: bool = serial_trigger_enable
        self._raw_reading_enable: bool = raw_reading_enable
        self._trigger_char: bytes = trigger_char
        # input command mapping
        self.cmds = {
            'open_menu': b'x',  # no eol
            'close_menu': b'x',  # no eol
            'tare': b'1',  # no eol
            'calibrate': b'2',  # no eol, leads to increment/decrement -> 'x' to close
            'increment': b'+',  # no eol, leads to increment/decrement -> 'x' to close
            'decrement': b'-',  # no eol, leads to increment/decrement -> 'x' to close
            'timestamp': b'3',  # no eol, toggles between enabled/disabled
            'report_rate': b'4',  # no eol, leads to increment/decrement -> 'x' to close
            'baud': b'5',  # requires EOL, enter a quantity
            'units': b'6',  # no eol, toggles between lbs and kg
            'decimals': b'7',  # no eol, leads to increment/decrement -> 'x' to close
            'avg_amt': b'8',  # no eol, leads to increment/decrement -> 'x' to close
            'local_temp': b'9',  # no eol, toggles between enabled/disabled
            'remote_temp': b'r',  # no eol, toggles between enabled/disabled
            'status_led': b's',  # no eol, toggles between enabled/disabled
            'serial_trigger': b't',  # no eol, toggles between enabled/disabled
            'raw_reading': b'q',  # no eol, toggles between enabled/disabled
            'trigger_char': b'c',  # no eol, next char entered is the new trigger char
        }
        self.load_config_from_device()

    def session(self, func):
        """
        decorator to ensure a complete session of editing the OpenScale
        """

        @wraps(func)
        def wrapper():
            if not self.is_open:
                self.open()
            # keep separate to help timings
            self.reset_output_buffer()
            self.write(self.cmds['open_menu'])
            self.flush()
            self.reset_input_buffer()
            try:
                return func()
            except Exception as e:
                print(e)
            finally:
                self.write(self.cmds['close_menu'])

        return wrapper

    @session
    def load_config_from_device(self):
        res = self.parse_menu_response()
        # noinspection SpellCheckingInspection
        self.baudrate = res['baud']
        self._tare = res['tare']
        self._timestamp_enable = res['timestamp']
        self._local_temp_enable = res['local_temp_enable']
        self._remote_temp_enable = res['remote_temp_enable']
        self._cal_value = res['calibrate']
        self._report_rate = res['report_rate']
        self._units = res['units']
        self._decimal_places = res['decimal_places']
        self._num_avgs = res['num_avg']
        self._status_led = res['status_led']
        self._serial_trigger_enable = res['serial_trigger_enable']
        self._raw_reading_enable = res['raw_reading']
        self._trigger_char = res['trigger_char']

    @session
    def parse_menu_response(self):
        raw_res = self.read_until(b'>').decode("utf-8").split('\r\n')
        res = {
            'tare': None,
            'calibrate': None,
            'timestamp': None,
            'report_rate': None,
            'baud': None,
            'units': None,
            'decimal_places': None,
            'num_avg': None,
            'local_temp_enable': None,
            'remote_temp_enable': None,
            'status_led': None,
            'serial_trigger_enable': None,
            'raw_reading': None,
            'trigger_char': None,
        }
        for line, index_tuple in zip(raw_res, self.prompt_indexes):
            res[index_tuple[0]] = line[index_tuple[1]:-1]
        res['baud'] = int(res['baud'][:-4])
        res['trigger_char'] = chr(int(res['trigger_char']))
        for key in ('tare', 'calibrate', 'report_rate', 'decimal_places', 'num_avg'):
            res[key] = int(res[key])
        for key in ('timestamp', 'local_temp_enable', 'remote_temp_enable',
                    'status_led', 'serial_trigger_enable', 'raw_reading'):
            res[key] = False if res[key] == 'Off' else True
        return res

    def triggered_read(self):
        self.write(self.trigger_char)

    @property
    def timestamp_enable(self):
        return self._timestamp_enable

    @timestamp_enable.setter
    @session
    def timestamp_enable(self, enable: bool):
        if self._timestamp_enable != enable:
            self.write(self.cmds['timestamp'])
            self._timestamp_enable = enable

    @property
    def report_rate(self):
        return self._report_rate

    @report_rate.setter
    def report_rate(self, value: int):
        diff = self._report_rate - value
        if diff == 0:
            return
        elif diff > 0:  # decrement `diff` times
            self.write(self.cmds['report_rate'])
            for i in range(1, diff):
                self.write(self.cmds['decrement'])
            self.reset_input_buffer()
        elif diff < 0:  # increment `diff` times
            self.write(self.cmds['report_rate'])
            for i in range(1, diff):
                self.write(self.cmds['increment'])
            self.reset_input_buffer()

    @property
    def calibrate(self):
        return self._cal_value

    @calibrate.setter
    def calibrate(self, value: int):
        diff = self._cal_value - value
        if diff == 0:
            return
        elif diff > 0:  # decrement `diff` times
            self.write(self.cmds['calibrate'])
            for i in range(1, diff):
                self.write(self.cmds['decrement'])
            self.reset_input_buffer()
        elif diff < 0:  # increment `diff` times
            self.write(self.cmds['calibrate'])
            for i in range(1, diff):
                self.write(self.cmds['increment'])
            self.reset_input_buffer()

    @property
    def trigger_char(self):
        return self._trigger_char

    @trigger_char.setter
    @session
    def trigger_char(self, char: (str, bytes)) -> None:
        if len(char) != 1:
            raise ValueError('length of trigger char must be 1')
        self._trigger_char = bytes(char)
        self.write(self.cmds['trigger_char'])
        self.write(self._trigger_char)

    @property
    def local_temp_enable(self):
        return self._local_temp_enable

    @local_temp_enable.setter
    @session
    def local_temp_enable(self, enable: bool):
        if self._local_temp_enable != enable:
            self.write(self.cmds['local_temp'])
            self._remote_temp_enable = enable

    @property
    def remote_temp_enable(self):
        return self._remote_temp_enable

    @remote_temp_enable.setter
    @session
    def remote_temp_enable(self, enable: bool):
        if self._remote_temp_enable != enable:
            self.write(self.cmds['remote_temp'])
            self._remote_temp_enable = enable

    @property
    def units(self):
        return self._units

    @units.setter
    @session
    def units(self, unit: str):
        if self._units != unit:
            self.write(self.cmds['units'])
            self._units = unit

    @property
    def decimals(self):
        return self._decimal_places

    @decimals.setter
    def decimals(self, places: int):
        if self._decimal_places != places:
            self.write(self.cmds['decimals'])
            self._decimal_places = places

    @property
    def num_avgs(self):
        return self._num_avgs

    @num_avgs.setter
    @session
    def num_avgs(self, n_avgs: int):
        if self._num_avgs != n_avgs:
            self.write(self.cmds['avg_amt'])
            self.write(n_avgs)
            self._num_avgs = n_avgs

    @property
    def status_led(self):
        return self._status_led

    @status_led.setter
    @session
    def status_led(self, enable: bool):
        if self._status_led != enable:
            self.write(self.cmds['status_led'])
            self._status_led = enable

    @property
    def raw_reading_enable(self):
        return self._raw_reading_enable

    @raw_reading_enable.setter
    @session
    def raw_reading_enable(self, enable: bool):
        if self._raw_reading_enable != enable:
            self.write(self.cmds['raw_reading'])
            self._raw_reading_enable = enable

    @property
    def serial_trigger_enable(self):
        return self._serial_trigger_enable

    @serial_trigger_enable.setter
    @session
    def serial_trigger_enable(self, enable: bool):
        if self._serial_trigger_enable != enable:
            self.write(self.cmds['serial_trigger'])
            self._serial_trigger_enable = enable

    @session
    def tare(self) -> Tuple[int, int]:
        """tares scale and returns tare offset(s)"""
        # b'\n\rTare point 1: [\d+]\r\n'\
        # b'\n\rTare point 2: [\d+]\r\n'
        self.write(self.cmds['tare'])
        self.read_until(b'Tare point 1: ')  # toss first line
        tare_val_1: int = int(self.read_until(b'\r\n').strip())
        self.read_until(b'Tare point 2: ')  # toss first line
        tare_val_2: int = int(self.read_until(b'\r\n').strip())
        return tare_val_1, tare_val_2

    @session
    def read_cal_info(self) -> Dict[str, Union[float, str, int]]:
        """begins interactive calibration process. Returns end result calibration value"""
        # b'Scale calibration\r\n'\
        # b'Remove all weight from scale\r\n'
        # b'After readings begin, place known weight on scale\r\n'\
        # b'Press + or a to increase calibration factor\r\n'\
        # b'Press - or z to decrease calibration factor\r\n'\
        # b'Press 0 to zero factor\r\n'\
        # b'Press x to exit\r\n'
        # b'Reading: [\d+.\d+] [lbs|kg] ]   Calibration Factor: \d+\r\n'
        #
        # behaviour in loop:
        # -> b'+' | b'-' | b'0' | b'a' | b'z' => b'Reading: [\d+.\d+] [lbs|kg] ]   Calibration Factor: \d+\r\n'
        # -> b'x' => <save_and_exit>
        self.write(self.cmds['calibrate'])
        self.read(240)  # initial spiel is 240 bytes
        response = self.read_until(b'\r\n').decode('utf-8').split()
        # index: contents
        # 0: string float reading in lbs|kg
        # 1: string for units
        # 2: 'Calibration'
        # 3: 'Factor:'
        # 4: string reading of integer offset used internally
        res = {
            'reading': float(response[0]),
            'units': str(response[1]),
            'cal_factor': int(response[4]),
        }
        return res

    def get_reading(self) -> Tuple:
        # order is (if enabled) : comma separation, no whitespace:
        # timestamp -- toggleable -- int
        # calibrated_reading -- always printed -- float
        # units -- always printed -- str
        # raw_reading -- toggleable -- int
        # local_temp -- toggleable -- float
        # remote_temp -- toggleable -- float
        ret_map = {
            # order: ret     (timestamp,  cal,     unit, raw, local, remote)
            0b01000: lambda x: (None, float(x[0]), x[1], None, None, None),
            0b01001: lambda x: (None, float(x[0]), x[1], None, None, float(x[2])),
            0b01010: lambda x: (None, float(x[0]), x[1], None, float(x[2]), None),
            0b01011: lambda x: (None, float(x[0]), x[1], None, float(x[2]), float(x[3])),
            0b01100: lambda x: (None, float(x[0]), x[1], int(x[2]), None, None),
            0b01101: lambda x: (None, float(x[0]), x[1], int(x[2]), None, float(x[3])),
            0b01110: lambda x: (None, float(x[0]), x[1], int(x[2]), float(x[3]), None),
            0b01111: lambda x: (None, float(x[0]), x[1], int(x[2]), float(x[3]), float(x[4])),
            0b11000: lambda x: (int(x[0]), float(x[1]), x[2], None, None, None),
            0b11001: lambda x: (int(x[0]), float(x[1]), x[2], None, None, float(x[3])),
            0b11010: lambda x: (int(x[0]), float(x[1]), x[2], None, float(x[3]), None),
            0b11011: lambda x: (int(x[0]), float(x[1]), x[2], None, float(x[3]), float(x[4])),
            0b11100: lambda x: (int(x[0]), float(x[1]), x[2], int(x[3]), None, None),
            0b11101: lambda x: (int(x[0]), float(x[1]), x[2], int(x[3]), None, float(x[4])),
            0b11110: lambda x: (int(x[0]), float(x[1]), x[2], int(x[3]), float(x[4]), None),
            0b11111: lambda x: (int(x[0]), float(x[1]), x[2], int(x[3]), float(x[4]), float(x[5])),
        }

        key = (self._timestamp_enable << 4) | \
              0b01000 | \
              (self._raw_reading_enable << 2) | \
              (self._local_temp_enable << 1) | \
              self._remote_temp_enable
        self.triggered_read()
        res = self.read_until(b'\r\n').decode('utf-8').split(',')
        return ret_map[key](res)
