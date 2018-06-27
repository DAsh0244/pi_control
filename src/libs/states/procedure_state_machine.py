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

# noinspection PyUnresolvedReferences
import sys
import yaml
from typing import List
# from transitions.extensions import GraphMachine as Machine
# from transitions import Machine

from actions import actions
from libs.hal import set_config


# import logging
#
# logging.basicConfig(level=logging.DEBUG)
# # Set transitions' log level to INFO; DEBUG messages will be omitted
# logging.getLogger('transitions').setLevel(logging.INFO)


# noinspection SpellCheckingInspection
class BaseYamlConstruct(yaml.YAMLObject):
    type = None

    def __repr__(self):
        return '{!s}({!s})'.format(self.__class__.__name__,
                                   ', '.join('{!s}={!r}'.format(k, v) for k, v in vars(self).items()))


class Action(BaseYamlConstruct):
    """
    actions are defined as having:
        a base function to be called
        a set of params to pass to function
        and a mapping describing transition rules allowed for the action
    """
    yaml_tag = '!Action'
    type = 'ACT'

    def __init__(self, name: str, nxt: dict, params=None):
        self.name = name
        self.params = params
        self.nxt = nxt
        # self.nxt = {k: actions[v] for k, v in nxt.items()}

    def execute(self):
        return actions[self.name](params=self.params, nxt=self.nxt)


# end sentinel
END_ACTION = Action(name='Complete', nxt={'success': None})


class Routine(BaseYamlConstruct):
    yaml_tag = '!Routine'
    type = 'RTN'

    def __init__(self, name: str, units: str, actions: List[Action], output: str = 'stdout'):
        self.name = name
        self.units = units
        self.actions = actions
        self.output = output
        # self.machine = self.generate_state_machine()
        # self.machine.add_ordered_transitions()

    @property
    def steps(self):
        for action in self.actions:
            yield action
        else:
            yield END_ACTION

    # def generate_states(self):
    #     """
    #     parser a routine, identifies all needed states as defined in routine transitions, creates a transition object
    #     :return: mapping for transitions
    #     """
    #     # act: Action
    #     states = {str(k) for act in self.actions for k in act.nxt.values()}
    #     return list(states)
    #
    # def generate_state_machine(self):
    #     states = self.generate_states()
    #     transition_table = []
    #     for action in self.actions:
    #         for condition, val in action.nxt.items():
    #             transition_table.append({'trigger': 'next_state',
    #                                      'source': action.name,
    #                                      'dest': val,
    #                                      # 'conditions': str(condition),
    #                                      # 'unless': ['condition1', 'condition2'] ,
    #                                      })
    #         pprint(transition_table)
    #         print('')
    #     return Machine(model=self,
    #                    states=states,
    #                    transitions=transition_table,
    #                    # title=self.name,
    #                    initial=self.actions[0].name,
    #                    # show_conditions=True
    #                    )
    #     #     {'trigger': 'evaporate', 'source': 'liquid', 'dest': 'gas', 'conditions': 'is_valid'},
    #     #     {'trigger': 'sublimate', 'source': 'solid', 'dest': 'gas', 'unless': 'is_not_valid'},
    #     #     {'trigger': 'ionize', 'source': 'gas', 'dest': 'plasma',
    #     #      'conditions': ['is_valid', 'is_also_valid']}


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


def register_routine():
    return None


def register_action():
    return None


DOC_DISPATCHER = {
    'CFG': set_config,
    'RTN': register_routine,
    'ACT': register_action,
}


def load_config(path):
    # from code import interact
    from pprint import pprint
    with open(path, 'r') as file:
        # docs = yaml.load(file)
        docs = yaml.load_all(file)
        cfg = {}
        for doc in docs:
            cfg = eval(repr(doc))
            pprint(cfg)
            for routine in cfg['ROUTINES']:
                for step in routine.steps:
                    current_step = step
                    print(current_step)
                    if current_step is not END_ACTION:
                        current_step = current_step.execute()
                        print(current_step)
                # pprint(routine.generate_states())
                # interact(local=locals())
        # DOC_DISPATCHER[doc.__type](doc)
        return cfg


if __name__ == '__main__':
    load_config('../../test/test_config.yaml')
