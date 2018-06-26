#! /usr/bin/env python
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
pi_control
procedure_state_machine.py
Author: Danyal Ahsanullah
Date: 6/26/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: 
"""

import sys
import yaml
# import transitions

from libs.utils import ReprMixIn
from libs.hal import set_config
from actions import actions

from typing import Iterable


class BaseYaml(yaml.YAMLObject, ReprMixIn):
    type = None
    pass


class Action(BaseYaml):
    """
    actions are defined as having:
        a base function to be called
        a set of params to pass to function
        and a mapping describing transition rules allowed for the action
    """
    yaml_tag = '!Action'
    _type = 'ACT'

    def __init__(self, name: str, nxt: dict, params=None):
        self.action = actions[name]
        self.params = params
        self.nxt = nxt


class Routine(BaseYaml):
    yaml_tag = '!Routine'
    type = 'RTN'
    output_map = {'stdout': sys.stdout,
                  'stderr': sys.stderr,
                  }

    def __init__(self, name: str, units: str, actions: Iterable[Action], output: str = 'stdout'):
        self.name = name
        self.units = units
        self.actions = actions
        self.output = self.output_map.get(output, open(output, 'w'))

    def __del__(self):
        self.output.close()

    def generate_states(self):
        """
        parser a routine, identifies all needed states as defined in routine transitions, creates a transition object
        :return: mapping for transitions
        """
        # act: Action
        states = {str(k) for act in self.actions for k in act.nxt.values()}
        return states


# TODO: figure out validation -- looks like have to define a method in the from_yaml hook
class Config(BaseYaml):
    yaml_tag = '!Config'
    _type = 'CFG'
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


def register_routine():
    return None


def register_action():
    return None


DOC_DISPATCHER = {
    'CFG': set_config,
    'RTN': register_routine,
    'ACT': register_action,
}

if __name__ == '__main__':
    from pprint import pprint


    def load_config(path):
        with open(path, 'r') as file:
            docs = yaml.load_all(file)
            cfg = {}
            for doc in docs:
                cfg = eval(repr(doc))
                pprint(cfg)
                for routine in doc['ROUTINES']:
                    pprint(routine.generate_states())

            # DOC_DISPATCHER[doc.__type](doc)

            return cfg


    load_config('../../test/test_config.yaml')
