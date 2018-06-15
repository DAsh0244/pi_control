# util.py
# utility misc functions

# noinspection PyUnresolvedReferences
import yaml as cfg_formatter
from hal import ActuatorConfig, ADC  # , DAC


# human readable conversion functions
def level2voltage(level):
    return level * ADC.step_size


def level2position(level):
    return level * ActuatorConfig.distance_per_level


def mm2in(mm_len):
    return mm_len * 0.0393701


def in2mm(in_len):
    return in_len * 25.4


def lbs2kg(lbs):
    return lbs * 0.453592


def kg2lbs(kg):
    return kg * 2.20462


# log file handling
def cleanup_log(logfile):
    """
    base cleanup function that provides basic file cleanup for formatting things like timesteps
    """
    raise NotImplementedError()
