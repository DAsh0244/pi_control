# util.py
# utility misc functions

# noinspection PyUnresolvedReferences
import warnings as _warnings
from random import randint as _randint
# noinspection PyUnresolvedReferences
import yaml
import yaml as cfg_formatter


def nop(*args, **kwargs):
    """function that matches any prototype and proceeds to do nothing"""
    pass


def sop(*args, **kwargs):
    """function that matches any prototype and just returns a random int"""
    return _randint(0, 2 ** 15 - 1)


def warning_on_one_line(message, category, filename, lineno, file=None, line=None):
    return '%s:%s: %s: %s\n\n' % (filename, lineno, category.__name__, message)


_warnings.formatwarning = warning_on_one_line


# human readable conversion functions
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


def get_k_value(k_subscript):
    k = 0
    prompt = 'Enter Desired K{} Value: '.format(k_subscript)
    while True:  # delay int conversion to handle invalid string inputs
        val = input(prompt).strip()
        try:
            from math import isnan, isinf
            k = float(val)
            if isnan(k) or isinf(k):
                raise ValueError()
            return k
        except ValueError:
            pass


def load_config(cfg_path):
    with open(cfg_path, 'r') as cfg_file:
        config = cfg_formatter.load(cfg_file)
    # for key, val in config.items():
    #     globals()[key] = val
    return config
    # from pprint import pprint
    # pprint(globals())


def save_config(cfg_path):
    pass
    # with open(cfg_path, 'w') as cfg_file:
    #     cfg_formatter.dump({'POS_LIMIT_LOW': actuator.pos_limit_low,
    #                         'POS_LIMIT_HIGH': actuator.pos_limit_high,
    #                         'POS_THRESHOLD_LOW': actuator.pos_threshold_low,
    #                         'POS_THRESHOLD_HIGH': actuator.pos_threshold_high,
    #                         'SAMPLE_RATE': adc.sample_rate,
    #                         'TIMEOUT': 10,
    #                         'UNITS': UNITS,
    #                         'OUTFILE': 'test.txt',
    #                         },
    #                        cfg_file
    #                        )


def edit_config(cfg_path):
    pass


class BaseYamlConstruct(yaml.YAMLObject):
    type = None

    def __repr__(self):
        return '{!s}({!s})'.format(self.__class__.__name__,
                                   ', '.join('{!s}={!r}'.format(k, v) for k, v in vars(self).items()))
