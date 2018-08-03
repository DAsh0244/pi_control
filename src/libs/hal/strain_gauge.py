#! /usr/bin/env python
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
pi_control
strain_gauge.py
Author: Danyal Ahsanullah
Date: 7/25/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: 
"""
import numpy as np

from libs.data_router import add_to_poll, publish
from libs.hal.adc import ADS1115Interface as A2D

if __name__ == '__main__':
    pass


class StrainGauge:
    def __init__(self, interface: A2D, vcc: float = 5.0, gf: float = 2.0, r_nom: float = 350.0):
        self.interface = interface
        self.vcc = vcc
        self.gf = gf
        self.r_nom = r_nom
        self.cal_map = np.array([[], []])
        add_to_poll(self.read_strain)

    @publish('strain', ('strain',))
    def read_strain(self):
        raw = self.interface.read_adc_difference(3, gain=4, data_rate=860)
        strain = raw
        # voltage = self.interface.level2voltage(raw) # + (self.vcc / 2)
        # strain = .8 / (2*((1+voltage) - (.4*voltage-1))) * (1+ (1/350))
        #strain = (1 / voltage - 1) / self.gf
        return strain

    @publish('strain', ('strain',))
    def read_adjusted_strain(self):
        """
        tries applying a linear piecewise interpolated to the read strain value as a correction factor.
        :return:
        """
        strain = self.read_strain()
        correction = np.interp(strain, self.cal_map[:, 0], self.cal_map[:, 1])
        return strain + correction

    def add_cal_point(self, target):
        """
        Call after the system is strained to a known strain value
        successive calls with differing strain targets help form a better curve

        recommendation is to call multiple times at various strains.
        """
        strain = self.read_strain()
        diff = (target - strain)
        self.cal_map = np.vstack((self.cal_map, [target, diff]))
