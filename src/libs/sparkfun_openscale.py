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
Description:
"""

import serial


class OpenScale(serial.Serial):
    BAUD_MIN = 1200
    BAUD_MAX = 1000000
    # prompt for initial opening of config menu:
    #
    # b'1) Tare scale to zero [\d+]\n'\
    # b'2) Calibrate scale[\d+]\n'\
    # b'3) Timestamp [On|Off]\n'\
    # b'4) Set report rate [\d+]\n'\
    # b'5) Set baud rate [\d+ bps]\n'\
    # b'6) Change units of measure [lbs|kg]\n'\
    # b'7) Decimals [\d+]\n'\
    # b'8) Average amount [\d+]\n'\
    # b'9) Local temp [On|Off]\n'\
    # b'r) Remote temp [On|Off]\n'\
    # b's) Status LED [Blink|Off]\n'\
    # b't) Serial trigger [On|Off]\n'\
    # b'q) Raw reading [On|Off]\n'\
    # b'c) Trigger character: [\d+]\n'\
    # b'x) Exit'\
    # b'>\n'

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

    end_interactive_prompt = b'>\n'

    def __init__(self, report_rate: int = 200, units: str = 'kg', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._trigger_char: bytes = b'0'
        self._cal_value: int = 0
        self.report_rate: int = report_rate
        self.decimal_places = 0
        self._num_avgs = 3

        self._timestamp_enable: bool = True
        self._local_temp_enable: bool = False
        self._remote_temp_enable: bool = False
        self._serial_trigger_enable: bool = True
        self._raw_reading_enable: bool = True
        self._status_lef = True

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
        if not self.is_open:
            self.open()

        self.write(self.cmds['open_menu'])
        res = self.parse_menu_response()
        if res['units'] != units:
            self.write(self.cmds['units'])
        self.tare()

    def parse_menu_response(self):
        raw_res = self.read_until(b'>\n').decode("utf-8").split('\n')
        res = {}
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

    @property
    def trigger_char(self):
        return self._trigger_char

    @trigger_char.setter
    def trigger_char(self, char: (str, bytes)):
        if len(char) > 1:
            raise ValueError('length of trigger char must be 1')
        self._trigger_char = bytes(char)
        if not self.is_open:
            self.open()
        self.write(self.cmds['trigger_char'])
        self.write(self._trigger_char)

    @property
    def local_temp_enable(self):
        return self._trigger_char

    @local_temp_enable.setter
    def local_temp_enable(self, enable: bool):
        if not self.is_open:
            self.open()
        self._local_temp_enable = enable
        if enable == self.write(self.cmds['local_temp']):
            pass

    def send_cmd(self, cmd: str, *args):
        self.write(self.cmds[cmd])
        if cmd in {'calibrate', 'increment', 'decrement', 'decimals', 'avg_amt', 'trigger_char'}:
            pass

    def tare(self) -> int:
        """tares scale and returns tare offset"""
        pass

    def calibrate(self):
        """begins interactive calibration process. Returns end result calibration value"""
        pass
