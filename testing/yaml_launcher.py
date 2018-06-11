#! /usr/bin/env python3
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
pi_control
data_structs.py
Author: Danyal Ahsanullah
Date: 6/11/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: yaml data structures definitions. file that parses and executes directives included
in the specified yaml configuration file
"""

import yaml

import hal
from cli_parser import actions as action_map


DOC_DISPATCHER = {'CFG': hal.set_config,
                  'RTN': hal.register_routine,
                  'ACT': hal.register_action,
                  }


def load_config(path):
    with open(path, 'r') as file:
        docs = yaml.load_all(file)
        for doc in docs:
            DOC_DISPATCHER[doc.__type](doc)


class Config(yaml.YAMLObject):
    yaml_tag = '!Config'
    __type = 'CFG'

    def __init__(self, version, units, upper_limit, lower_limit, adc_sample_rate, adc_gain, adc_channel):
        self.version = version
        self.units = units
        self.upper_limit = upper_limit
        self.lower_limit = lower_limit
        self.adc_sample_rate = adc_sample_rate
        self.adc_gain = adc_gain  # configurable, value must be one of: 2/3, 1, 2, 4, 8, 16
        self.adc_channel = adc_channel  # configurable, value must be one of: 0, 1, 2, 3

    def __repr__(self):
        return '{!s}({!s})'.format(self.__class__.__name__,
                                   repr(','.join('{!s}={!r}'.format(k, v) for k, v in vars(self).items()))[1:-1])


class Routine(yaml.YAMLObject):
    yaml_tag = '!Routine'
    __type = 'RTN'

    def __init__(self, name, units, actions, output='stdout'):
        self.name = name
        self.units = units
        self.actions = actions
        self.output = output

    def __repr__(self):
        return '{!s}({!s})'.format(self.__class__.__name__,
                                   repr(','.join('{!s}={!r}'.format(k, v) for k, v in vars(self).items()))[1:-1])


class Action(yaml.YAMLObject):
    yaml_tag = '!Action'
    __type = 'ACT'

    def __init__(self, name, params=None):
        self.action = action_map[name]
        self.params = params

    def __repr__(self):
        return '{!s}({!s})'.format(self.__class__.__name__,
                                   repr(','.join('{!s}={!r}'.format(k, v) for k, v in vars(self).items()))[1:-1])

__all__ = ['load_config']  # , 'DOC_DISPATCHER']
