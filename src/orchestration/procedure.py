#! /usr/bin/env python
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
pi_control
procedure.py
Author: Danyal Ahsanullah
Date: 6/26/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: 
"""

import yaml
from sys import exit as _exit
from collections.abc import Mapping as _Mapping
from typing import Iterable as _Iterable, Dict as _Dict

from libs.data_router import DataLogger
from libs.utils import yamlobj, ReprMixIn
from libs.hal import hal_cleanup, A2D, actuator
from orchestration.routines import Routine
from orchestration.actions import END_ACTION, ERROR_ACTION


@yamlobj('!Config')
class Config(_Mapping, ReprMixIn):
    type = 'CFG'
    accepted_units = {'raw', 'in', 'mm', 'N', 'lbf'}  # raw: A/D levels, imperial: in, lbf, metric: m, N
    accepted_adc_sample_rates = A2D.accepted_sample_rates
    accepted_adc_gains = A2D.accepted_gains
    accepted_adc_channels = A2D.accepted_channels

    def __init__(self, version, len_units, force_units, upper_limit, lower_limit, pos_adc_sample_rate, pos_adc_gain,
                 strain_adc_sample_rate, strain_adc_gain, pos_adc_channel=1, strain_adc_channel=3, period: float = 0.1):
        # validation starts at units, version must exist
        if any(unit in self.accepted_units for unit in (len_units, force_units)) and version:
            # to be used for future releases
            self.version = version
            # units to use for input/output values. internally math is done independent of units
            self.len_units = len_units
            self.force_units = force_units
            self.period = period
            # limits for actuator, stored and used in calculations as raw adc level
            self.upper_limit = actuator.convert_units[self.len_units](upper_limit)
            self.lower_limit = actuator.convert_units[self.len_units](lower_limit)
            # configuration for position adc channel
            if pos_adc_sample_rate in self.accepted_adc_sample_rates:
                self.pos_adc_sample_rate = pos_adc_sample_rate
            else:
                raise ValueError('Invalid sample rate provided: {!s}'.format(pos_adc_sample_rate))
            if pos_adc_gain in self.accepted_adc_gains:
                self.pos_adc_gain = pos_adc_gain
            else:
                raise ValueError('Invalid gain provided: {!s}'.format(pos_adc_gain))
            if pos_adc_channel in self.accepted_adc_channels:
                self.pos_adc_channel = pos_adc_channel
            else:
                raise ValueError('Invalid channel provided: {!s}'.format(pos_adc_channel))
            # configuration for strain gauge adc channel
            if strain_adc_sample_rate in self.accepted_adc_sample_rates:
                self.strain_adc_sample_rate = strain_adc_sample_rate
            else:
                raise ValueError('Invalid sample rate provided: {!s}'.format(strain_adc_sample_rate))
            if strain_adc_gain in self.accepted_adc_gains:
                self.strain_adc_gain = strain_adc_gain
            else:
                raise ValueError('Invalid gain provided: {!s}'.format(strain_adc_gain))
            if strain_adc_channel in self.accepted_adc_channels:
                self.strain_adc_channel = strain_adc_channel
            else:
                raise ValueError('Invalid differential channel provided: {!s}'.format(strain_adc_channel))
        else:
            raise ValueError('Bad YAML configuration')

    def __iter__(self):
        for entry in ('version', 'len_units', 'force_units', 'upper_limit', 'lower_limit',
                      'pos_adc_sample_rate', 'pos_adc_gain', 'pos_adc_channel',
                      'strain_adc_sample_rate', 'strain_adc_gain', 'strain_adc_channel'):
            yield entry

    def __len__(self):
        return 11

    def __getitem__(self, item):
        # print(self.__dict__)
        return self.__dict__[item]


def load_procedure(path):
    # from code import interact
    from pprint import pprint
    with open(path, 'r') as file:
        cfg = yaml.load(file)
        pprint(cfg)
        return cfg


class ProcedureExecutor:
    """
    class that handles executing routines
    """

    routines = []

    def __init__(self, cfg: _Dict, routines: _Iterable[Routine]):
        self.routines.extend(routines)
        self.logger = DataLogger(config=cfg)

    def run(self):
        import time
        start = time.time()
        for routine in self.routines:
            print('executing routine: {}'.format(routine.name))
            self.execute_routine(routine)
        print(time.time() - start)

    @staticmethod
    def execute_routine(routine):
        if not routine.exec:
            # routine is not meant to be executed
            print('routine not set for exec')
            return
        # start on start state
        transitions = routine.transitions
        current_action = routine.actions['START']
        status = 'not_started'
        try:
            while current_action is not END_ACTION:
                status = current_action.execute()
                # print(status, current_action.name, transitions)
                # #todo: remove if not simulating
                # from time import sleep
                # from random import uniform
                # sleep(uniform(0.05,5))
                # process status like for boolean actions
                if status == 'error':
                    # raise warning
                    ERROR_ACTION.execute()
                    break
                if '*' in transitions[current_action.name]:
                    status = '*'
                current_action = routine.actions[transitions[current_action.name][status]]
        except RuntimeError as e:  # error states trigger a runtime Error
            print(e)
            print('ERROR during {} with {} (status of {})'.format(routine.name, current_action.name, status))
            hal_cleanup()
            _exit(1)


if __name__ == '__main__':
    # config = load_config('../../test/test_config.yaml')
    from pprint import pprint

    # with open('../../test/test_config.yaml') as file:
    config = load_procedure('../../test/test_config.yaml')
    executor = ProcedureExecutor(cfg=config['CONFIG'], routines=config['ROUTINES'])
    executor.run()
