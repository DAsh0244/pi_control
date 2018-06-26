#! /usr/bin/env python3
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
pi_control
cli_parser.py
Author: Danyal Ahsanullah
Date: 6/11/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: parser definition for launching elastocaloric control script.
             yaml data structures definitions.
Usage:
    from cli_parser import parser, cmds, actions
       or
    from cli_parser import *
    ...
    args = parser.parse_args()
    if args['cmd'] = cmds['cmd_key_here']:
        ...
"""

import sys
import yaml
from argparse import ArgumentParser

from version import version as __version__
from libs.hal import adc, set_config, actuator
from routines import register_routine, register_action

# command names:
cmds = {'TEST_ADC': 'test_adc',
        'TEST_DAC': 'test_dac',
        'TEST_CAL': 'test_cal',
        'TEST_POS': 'test_pos',
        'RUN_ACQ': 'acquire',
        }

actions = {'RESET_MIN': 'reset_min',
           'RESET_MAX': 'reset_max',
           'GOTO_POS': 'set_pos',
           'CLEANUP': 'cleanup',
           }

parser = ArgumentParser()  # 'elastocaloric testing'
subparsers = parser.add_subparsers(help='Action to take', dest='cmd')
parser.add_argument('-V', '--version', action='version', version='%(prog)s {}'.format(__version__))
parser.add_argument('-t', '--timeout', type=int, default=5, help='set timeout for loop')
parser.add_argument('-r', '--sample_rate', type=int, choices=sorted(adc.accepted_sample_rates),
                    default=adc.sample_rate, help='Sample rate for adc (sps)')
parser.add_argument('-o', '--outfile', type=str, default=None, help='optional file to save results to')
parser.add_argument('--config', type=str, default=None, help='optional configuration file')
parser.add_argument('-u', '--unit', type=str, default='raw', choices={'raw', 'in', 'mm'},
                    help='unit to have final results in.')
# parser.add_argument('-g', '--gain', type=float, choices={2/3, 1, 2, 3, 8, 16}, default=1,
#                     help='adc input polarity (1, -1)')
# parser.add_argument('-c', '--channel', type=int, choices={1, 2, 3, 4}, help='adc input channel',
#                     default=ADC_CHANNEL)
# parser.add_argument('-a', '--alert_pin', type=int, default=21, help='RPI gpio pin number (eg: gpio27 -> "-a 27")')
# parser.add_argument('-v', '--verbose', action='count', default=0, help='verbosity')
# parser.add_argument('--help', action='help')

test_adc_parser = subparsers.add_parser(cmds['TEST_ADC'], help='test adc functionality')
test_dac_parser = subparsers.add_parser(cmds['TEST_DAC'], help='test dac functionality')
test_cal_parser = subparsers.add_parser(cmds['TEST_CAL'], help='test calibration routines')

test_positioning_parser = subparsers.add_parser(cmds['TEST_POS'], add_help=False, help='test controllable positing')
test_positioning_parser.add_argument('-L', '--low_min', type=int, default=actuator.pos_limit_low)
test_positioning_parser.add_argument('-l', '--low_threshold', type=int, default=actuator.pos_limit_low)
test_positioning_parser.add_argument('-h', '--high_threshold', type=int, default=actuator.pos_limit_high)
test_positioning_parser.add_argument('-H', '--high_max', type=int, default=actuator.pos_limit_high)
test_positioning_parser.add_argument('--help', action='help', help='print help')

pos_subparsers = test_positioning_parser.add_subparsers(help='specific position action to take', dest='action')
pos_subparsers.add_parser(actions['RESET_MIN'], help='reset to minimum extension')
pos_subparsers.add_parser(actions['RESET_MAX'], help='reset to max extension')

goto_parser = pos_subparsers.add_parser('goto_pos', help='go to desired position')
goto_parser.add_argument('position', type=int, default=adc.levels >> 1,
                         help='position value between 0 and {}'.format(adc.max_level))

monitor_parser = subparsers.add_parser(cmds['RUN_ACQ'], add_help=False, help='run acquisition')
monitor_parser.add_argument('-L', '--low_min', type=int, default=actuator.pos_limit_low)
monitor_parser.add_argument('-l', '--low_threshold', type=int, default=actuator.pos_limit_low)
monitor_parser.add_argument('-h', '--high_threshold', type=int, default=actuator.pos_limit_high)
monitor_parser.add_argument('-H', '--high_max', type=int, default=actuator.pos_limit_high)
monitor_parser.add_argument('--help', action='help', help='print help')

DOC_DISPATCHER = {
    'CFG': set_config,
    'RTN': register_routine,
    'ACT': register_action,
}


def load_config(path):
    with open(path, 'r') as file:
        docs = yaml.load_all(file)
        cfg = {}
        for doc in docs:
            cfg = eval(repr(doc))
            # DOC_DISPATCHER[doc.__type](doc)
        return cfg


class ReprMixIn:
    def __repr__(self):
        return '{!s}({!s})'.format(self.__class__.__name__,
                                   ', '.join('{!s}={!r}'.format(k, v) for k, v in vars(self).items()))


# TODO: figure out validation -- looks like have to define a method in the from_yaml hook
class Config(yaml.YAMLObject, ReprMixIn):
    yaml_tag = '!Config'
    __type = 'CFG'
    accepted_units = {'raw', 'imperial', 'metric'}  # raw: A/D levels, imperial: in, lb, metric: mm, kg
    accepted_adc_sample_rates = adc.accepted_sample_rates
    accepted_adc_gains = adc.accepted_gains
    accepted_adc_channels = adc.accepted_channels

    def __init__(self, version, units, upper_limit, lower_limit, adc_sample_rate, adc_gain, adc_channel):
        if units in self.accepted_units and \
                adc_sample_rate in self.accepted_adc_sample_rates and \
                adc_gain in self.accepted_adc_gains and \
                adc_channel in self.accepted_adc_channels:
            self.version = version  # to be used for future releases
            self.units = units  # units to use for input/output values. internally math is done independent of units
            self.upper_limit = upper_limit  # upper limit for actuator, stored and used in calculations as raw adc level
            self.lower_limit = lower_limit  # lower limit for actuator, stored and used in calculations as raw adc level
            self.adc_sample_rate = adc_sample_rate  # configurable, value must be: 8, 16, 32, 64, 128, 250, 475, 860
            self.adc_gain = adc_gain  # configurable, value must be: 2/3, 1, 2, 4, 8, 16
            self.adc_channel = adc_channel  # configurable, value must be: 0, 1, 2, 3
        else:
            raise ValueError('Bad key in yaml configuration.')


class Routine(yaml.YAMLObject, ReprMixIn):
    yaml_tag = '!Routine'
    __type = 'RTN'

    def __init__(self, name, units, actions, output=sys.stdout):
        self.name = name
        self.units = units
        self.actions = actions
        self.output = output


class Action(yaml.YAMLObject, ReprMixIn):
    yaml_tag = '!Action'
    __type = 'ACT'

    def __init__(self, name, params=None):
        self.action = actions[name]
        self.params = params


if __name__ == '__main__':
    from pprint import pprint

    parser.print_help()
    print('')
    pprint(load_config('test_config.yaml'))
