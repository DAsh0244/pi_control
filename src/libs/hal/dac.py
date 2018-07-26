"""
pi_control
dac.py
Author: Danyal Ahsanullah
Date: 7/25/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: 
"""

from collections import deque as _deque

from libs.hal.constants import GLOBAL_VCC

try:
    from Adafruit_MCP4725 import MCP4725
except ImportError:
    from libs.utils import nop as _nop
    import warnings as _warnings

    _warnings.warn('failed to load hardware interfaces for dac, using stub classes for syntax checking',
                   RuntimeWarning)


    class MCP4725:
        """quick stub class for mcp4725"""
        set_voltage = _nop


class MCP4725Interface(MCP4725):
    """
    MCP4725 wrapper with added convenience functionality
    """
    bits = 12
    levels = 1 << bits
    stop = 0

    def __init__(self, vcc=GLOBAL_VCC, *args, history_len=20, **kwargs):
        self.value_history = _deque(maxlen=history_len)  # holds previous values
        self.value = 0  # holds current value
        self.vcc = vcc
        self.step_size = vcc / self.levels
        self.default_val = self.levels >> 1  # default is 1/2 speed
        super().__init__(*args, **kwargs)

    def set_level(self, level):
        self.value_history.append(self.value)
        self.value = level
        super().set_voltage(self.value)

    def set_voltage(self, voltage):
        self.value_history.append(self.value)
        self.value = self.voltage2level(voltage)
        super().set_voltage(self.value)

    def level2voltage(self, level: int) -> float:
        """
        converts a discrete level to a corresponding voltage value
        :type level: int
        :param level: discrete level to convert to voltage
        :rtype: float
        :return: translated value
        """
        return level * self.step_size

    def voltage2level(self, voltage: float) -> int:
        return round(voltage / self.step_size)
