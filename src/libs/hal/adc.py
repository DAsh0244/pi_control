"""
pi_control
adc.py
Author: Danyal Ahsanullah
Date: 7/25/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: 
"""

from collections import deque as _deque

from libs.utils import GPIO
from libs.hal.constants import GLOBAL_VCC

try:
    from Adafruit_ADS1x15 import ADS1115
except ImportError:
    import warnings as _warnings
    from libs.utils import (
        nop as _nop,
        sop as _sop
    )

    _warnings.warn('failed to load hardware interfaces for adc, using stub classes for syntax checking',
                   RuntimeWarning)


    class ADS1115:
        """quick stub class for ADS1115"""
        stop_adc = _nop
        start_adc = start_adc_comparator = get_last_result = read_adc = read_adc_difference = _sop


class ADS1115Interface(ADS1115):
    """
    Extended ADS1115 interface with builtin convenience for configuration and reading
    """
    bits = 16
    levels = 1 << bits
    max_level = (levels >> 1) - 1
    min_level = -1 * (levels >> 1)
    pga_map = {2 / 3: 6.144,  # map of gain values vs max peak readable voltage
               1: 4.096,
               2: 2.048,
               4: 1.024,
               8: 0.512,
               16: 0.256,
               }
    accepted_sample_rates = {8, 16, 32, 64, 128, 250, 475, 860}
    accepted_gains = {2 / 3, 1, 2, 4, 8, 16}
    accepted_channels = {0, 1, 2, 3}

    def __init__(self, sample_rate: int = 128, gain: int = 1, vcc: float = GLOBAL_VCC, default_channel: int = 0,
                 alert_pin: int = 21, history_len: int = 20):
        """
        initialize the ADS1115 interface
        :type history_len: int
        :type alert_pin: int
        :type vcc: float
        :type default_channel: int
        :type gain: int
        :type sample_rate: int
        :param sample_rate: Sample rate (samples/sec) as an integer. Must be within: {8, 16, 32, 64, 128, 250, 475, 860}
        :param gain: Internal PGA gain, accepted values are: {2 / 3, 1, 2, 4, 8, 16}
        :param vcc: Supply voltage (V) usually 3.3 or 5
        :param default_channel: default input channel. Must be within {0, 1, 2, 3}
        :param alert_pin: Pin the ADC ALRT/RDY pin is tied to.
        :param history_len: how many previous values to keep. If value is exceeded, the oldest value is dropped.
        """
        self.vcc = vcc
        self.sample_rate = sample_rate
        self.gain = gain
        self.default_channel = default_channel
        self.alert_pin = alert_pin
        self.step_size = 2 * self.max_voltage / self.levels
        self.history: _deque = _deque(maxlen=history_len)
        super().__init__()

    def get_last_result(self):
        """
        returns contents of read register for device.
        Adds value to history
        :return: integer representing the voltage level
        """
        res = super().get_last_result()
        self.history.append(res)
        return res

    @property
    def max_voltage(self) -> float:
        """
        returns max readable voltage
        :rtype: float
        :return: max input voltage level (+/-) or supply if limited to that
        """
        return min(self.pga_map[self.gain], self.vcc)

    def start_conversions(self) -> int:
        """
        starts conversions with preset defaults
        :rtype: int
        :return: first reading from ADC
        """
        return self.start_adc_comparator(self.default_channel, self.max_level, self.min_level, gain=self.gain,
                                         data_rate=self.sample_rate)

    def wait_for_sample(self, timeout=2):
        """
        blocking call to wait for the adc's Alert pin to signal conversion ready
        :return: None
        """
        GPIO.wait_for_edge(self.alert_pin, GPIO.FALLING, timeout=timeout)

    def read_single(self) -> int:
        """
        reads a single-shot reading from the ADC
        :rtype: int
        :return: reading from ADC single shot reading
        """
        return self.read_adc(self.default_channel, gain=self.gain, data_rate=self.sample_rate)

    def level2voltage(self, level: int) -> float:
        """
        converts a discrete level to a corresponding voltage value
        :type level: int
        :param level: raw reading from ADC converted to voltage
        :rtype: float
        :return: translated value
        """
        return level * self.step_size

    def voltage2level(self, voltage: float) -> int:
        return round(voltage / self.step_size)

    def stop(self):
        super().stop_adc()
