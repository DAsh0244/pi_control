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

from typing import Iterable as _Iterable
from libs.utils import BaseYamlConstruct
from orchestration.actions import END_ACTION, ERROR_ACTION
from orchestration.routines import Routine


# import logging
#
# logging.basicConfig(level=logging.DEBUG)
# # Set transitions' log level to INFO; DEBUG messages will be omitted
# logging.getLogger('transitions').setLevel(logging.INFO)


# TODO: figure out validation -- looks like have to define a method in the from_yaml hook
class Config(BaseYamlConstruct):
    yaml_tag = '!Config'
    type = 'CFG'
    accepted_units = {'raw', 'imperial', 'metric'}  # raw: A/D levels, imperial: in, lb, metric: mm, kg

    # accepted_adc_sample_rates = adc.accepted_sample_rates
    # accepted_adc_gains = adc.accepted_gains
    # accepted_adc_channels = adc.accepted_channels

    def __init__(self, version, units, upper_limit, lower_limit, adc_sample_rate, adc_gain, adc_channel):
        self.version = version  # to be used for future releases
        self.units = units  # units to use for input/output values. internally math is done independent of units
        self.upper_limit = upper_limit  # upper limit for actuator, stored and used in calculations as raw adc level
        self.lower_limit = lower_limit  # lower limit for actuator, stored and used in calculations as raw adc level
        self.adc_sample_rate = adc_sample_rate  # configurable, value must be: 8, 16, 32, 64, 128, 250, 475, 860
        self.adc_gain = adc_gain  # configurable, value must be: 2/3, 1, 2, 4, 8, 16
        self.adc_channel = adc_channel  # configurable, value must be: 0, 1, 2, 3
        # if units in self.accepted_units and \
        #         adc_sample_rate in self.accepted_adc_sample_rates and \
        #         adc_gain in self.accepted_adc_gains and \
        #         adc_channel in self.accepted_adc_channels:
        # else:
        #     raise ValueError('Bad key in yaml configuration.')


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
            self.execute_routine(routine)

    @staticmethod
    def execute_routine(routine):
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
        except RuntimeError:
            print('ERROR during {} with {} (status of {})'.format(routine.name, current_action.name, status))


if __name__ == '__main__':
    # config = load_config('../../test/test_config.yaml')
    import yaml

    with open('../../test/test_config.yaml') as file:
        config = yaml.load(file)
        executor = ProcedureExecutor(config['ROUTINES'])
        executor.run()
