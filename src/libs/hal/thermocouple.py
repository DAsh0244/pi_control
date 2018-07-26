#! /usr/bin/env python
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
pi_control
thermocouple.py
Author: Danyal Ahsanullah
Date: 7/25/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: 
"""
from typing import Tuple
from libs.hal.max31856 import MAX31856
from libs.data_router import add_to_periodic_poll, publish


class Thermocouple(MAX31856):

    def __init__(self, name: str, tc_type, num_avgs, *args, **kwargs):
        super().__init__(tc_type=tc_type, avgsel=num_avgs, *args, **kwargs)
        self._tc_type_str = tc_type
        self._avg_samples = num_avgs
        self.name = name
        add_to_periodic_poll(self.get_temps)

    def read_temp(self):
        return super().read_temp_c()

    def read_internal_temp(self):
        return super().read_internal_temp_c()

    @publish('thermocouple', ('meta', 'temp', 'internal_temp'))
    def get_temps(self) -> Tuple[str, float, float]:
        return self.name, self.read_temp(), self.read_internal_temp()

    @property
    def fault_register(self):
        return super().read_fault_register()

    @property
    def thermocouple_type(self):
        return self._tc_type_str

    @thermocouple_type.setter
    def thermocouple_type(self, value):
        self._tc_type_str = value
        self.tc_type = self.THERMOCOUPLE_MAP[value]
        cr1 = ((self.avgsel << 4) + self.tc_type)
        self._write_register(self.MAX31856_REG_WRITE_CR1, cr1)

    @property
    def averaging_samples(self):
        return self._avg_samples

    @averaging_samples.setter
    def averaging_samples(self, value):
        self._avg_samples = value
        self.avgsel = self.SAMPLE_MAP[value]
        cr1 = ((self.avgsel << 4) + self.tc_type)
        self._write_register(self.MAX31856_REG_WRITE_CR1, cr1)
