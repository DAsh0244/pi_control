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

    def __init__(self, report_rate=200, units='kg', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trigger_char = None
        self.report_rate = report_rate
        self.cmd_eol = b'\n'
        self.cmds = {
            'open_menu': b'x',
            'close_menu': b'x',
            'tare': b'1',
            'calibrate': b'2',
            'calibrate_increase_weight': b'+',
            'calibrate_decrease_weight': b'-',
            'timestamp': b'3',
            'report_rate': b'4',
            'baud': b'5',
            'units': b'6',
            'units_lbs': b'0',
            'units_kg': b'1',
            'decimals': b'7',
            'avg_amt': b'8',
            'local_temp': b'9',
            'remote_temp': b'r',
            'status_led': b's',
            'serial_trigger': b't',
            'raw_reading': b'q',
            'trigger_char': b'c',
        }
        if not self.is_open:
            self.open()
        self.send_cmd('open_menu')
        self.send_cmd('units')
        self.send_cmd('kg')

    def send_cmd(self, cmd: str):
        self.write(self.cmds[cmd] + self.cmd_eol)
