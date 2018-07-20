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

import sys
from typing import Iterable as _Iterable

from libs.hal import hal_cleanup, A2D, actuator
from libs.utils import yamlobj, ReprMixIn
from orchestration.actions import END_ACTION, ERROR_ACTION
from orchestration.routines import Routine


# TODO: figure out validation
# https://github.com/an-oreo/pi_control/issues/6

@yamlobj('!Config')
class Config(ReprMixIn):
    type = 'CFG'
    accepted_units = {'raw', 'in', 'mm', 'N', 'lbf'}  # raw: A/D levels, imperial: in, lbf, metric: m, N
    accepted_adc_sample_rates = A2D.accepted_sample_rates
    accepted_adc_gains = A2D.accepted_gains
    accepted_adc_channels = A2D.accepted_channels

    def __init__(self, version, units, upper_limit, lower_limit, pos_adc_sample_rate, pos_adc_gain,
                 strain_adc_sample_rate, strain_adc_gain, pos_adc_channel=1, strain_adc_channel=3):
        # validation starts at units, version must exist
        if units in self.accepted_units and version:
            # to be used for future releases
            self.version = version
            # units to use for input/output values. internally math is done independent of units
            self.units = units
            # limits for actuator, stored and used in calculations as raw adc level
            self.upper_limit = actuator.convert_units[self.units.get('length', self.units)](upper_limit)
            self.lower_limit = actuator.convert_units[self.units.get('force', self.units)](lower_limit)
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


def load_config(path):
    # from code import interact
    from pprint import pprint
    with open(path, 'r') as file:
        docs = yaml.load(file)
        # docs = yaml.load_all(file)
        cfg = {}
        for doc in docs:
            cfg = eval(repr(doc))
            pprint(cfg)
        return cfg


class ProcedureExecutor:
    """
    class that handles executing routines
    """

    routines = []

    def __init__(self, routines: _Iterable[Routine]):
        self.routines.extend(routines)

    def run(self):
        for routine in self.routines:
            print('executing routine: {}'.format(routine.name))
            self.execute_routine(routine)

    def get_data(self):
        pass

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
                # process status like for boolean actions
                if status == 'error':
                    # raise warning
                    ERROR_ACTION.execute()
                    break
                if '*' in transitions[current_action.name]:
                    status = '*'
                current_action = routine.actions[transitions[current_action.name][status]]
        except RuntimeError:  # error states trigger a runtime Error
            print('ERROR during {} with {} (status of {})'.format(routine.name, current_action.name, status))
            hal_cleanup()
            sys.exit(1)


if __name__ == '__main__':
    # config = load_config('../../test/test_config.yaml')
    import yaml

    with open('../../test/test_config.yaml') as file:
        config = yaml.load(file)
        executor = ProcedureExecutor(config['ROUTINES'])
        executor.run()
