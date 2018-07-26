# utils.py

import numpy as _np
import yaml as _yaml

import warnings as _warnings
from numbers import Real as _Real
from functools import wraps as _wraps
from random import randint as _randint
from inspect import signature as _signature
from typing import Tuple, Dict, Union, Iterable

TS_PATTERN = "%Y_%m_%d_%H_%M_%S"


# noinspection PyUnusedLocal
def nop(*args, **kwargs):
    """function that matches any prototype and proceeds to do nothing"""
    pass


# noinspection PyUnusedLocal
def sop(*args, **kwargs):
    """function that matches any prototype and just returns a random int"""
    return _randint(0, 2 ** 15 - 1)


# noinspection PyUnusedLocal
def warning_on_one_line(message, category, filename, lineno, file=None, line=None):
    return '%s:%s: %s: %s\n\n' % (filename, lineno, category.__name__, message)


_warnings.formatwarning = warning_on_one_line

try:
    import RPi.GPIO as GPIO
    import Adafruit_GPIO.SPI as SPI
except ImportError:
    from time import sleep as _sleep

    _warnings.warn('failed to load RPi.GPIO, using stub class for syntax checking', RuntimeWarning)
    _warnings.warn('failed to load Adafruit_GPIO, using stub class for syntax checking', RuntimeWarning)


    # noinspection PyUnusedLocal,PyPep8Naming,SpellCheckingInspection
    class GPIO:
        """quick stub class for GPIO"""
        BCM = BOARD = IN = OUT = RISING = FALLING = BOTH = PUD_UP = PUD_DOWN = None
        setmode = setup = input = cleanup = add_event_detect = remove_event_detect = nop
        HIGH = 1
        LOW = 0

        @staticmethod
        def output(channel, level):
            return _randint(0, 1)

        @staticmethod
        def wait_for_edge(channel, edge, timeout):
            _sleep(timeout // 1000)


    # noinspection PyUnusedLocal,PyPep8Naming, SpellCheckingInspection
    class Adafruit_GPIO:
        """quick stub class for GPIO"""
        BCM = BOARD = IN = OUT = RISING = FALLING = BOTH = PUD_UP = PUD_DOWN = None
        setmode = setup = input = cleanup = add_event_detect = remove_event_detect = nop
        HIGH = 1
        LOW = 0

        @staticmethod
        def output(channel, level):
            return _randint(0, 1)

        get_platform_gpio = nop

        @staticmethod
        def wait_for_edge(channel, edge, timeout):
            _sleep(timeout // 1000)

        # provides hardware abstraction layer for easier access to hardware functions


    # noinspection PyUnusedLocal,PyPep8Naming, SpellCheckingInspection
    class SPI:
        MSBFIRST = 0

        class BitBang:
            def __init__(self, *args, **kwargs):
                pass

            set_clock_hz = set_mode = set_bit_order = transfer = nop

        SpiDev = BitBang


# human readable conversion functions
def mm2in(mm_len):
    return mm_len * 0.0393701


def in2mm(in_len):
    return in_len * 25.4


def lbs2kg(lbs):
    return lbs * 0.453592


def kg2lbs(kg):
    return kg * 2.20462


def kg2lbf(kg):
    # 2.20462 * 32.1740485564
    return kg * 70.9315509


def kg2N(kg):
    return 9.80665 * kg


def lbs2lbf(lbs):
    return 32.1740485564 * lbs


def lbs2N(lbs):
    # 4.448222 * 32.1740485564
    return 143.117311 * lbs


def lbf2N(lbf):
    return 4.448222 * lbf


def load_config(cfg_path):
    with open(cfg_path, 'r') as cfg_file:
        config = _yaml.load(cfg_file)
    # for key, val in config.items():
    #     globals()[key] = val
    return config['CONFIG']
    # from pprint import pprint
    # pprint(globals())


# noinspection PyUnusedLocal
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


# noinspection PyUnusedLocal
def edit_config(cfg_path):
    pass


class ReprMixIn:
    type = None

    def __repr__(self):
        return '{!s}({!s})'.format(self.__class__.__name__,
                                   ', '.join('{!s}={!r}'.format(k, v) for k, v in vars(self).items()))


def sinc_interp(x, s, u):
    """
    Interpolates x, sampled at "s" instants
    Output y is sampled at "u" instants ("u" for "upsampled")

    from Matlab:
    http://phaseportrait.blogspot.com/2008/06/sinc-interpolation-in-matlab.html
    """
    if len(x) != len(s):
        raise ValueError('x ({}) and s ({}) must be the same length'.format(len(x), len(s)))

    # Find the period
    t = s[1] - s[0]

    sinc_m = _np.tile(u, (len(s), 1)) - _np.tile(s[:, _np.newaxis], (1, len(u)))
    # noinspection PyUnresolvedReferences
    y = _np.dot(x, _np.sinc(sinc_m / t))
    return y


def yamlobj(tag):
    def wrapper(cls):
        def constructor(loader, node):
            fields = loader.construct_mapping(node)
            return cls(**fields)

        _yaml.add_constructor(tag, constructor)
        return cls
    return wrapper


def wrap_dict_ts(keys: Tuple[str]):
    """
    wraps the return tuple into a named dict following the order of the tuple provided via the :param keys: parameter.
    also adds a field 'ts' that holds a timestamp string
    :param keys: tuple of strings to be used as keys for the data values. note the order matters.
    :return: dictionary of the provided keys with associated data values
    """
    def _wrapper(func):
        fun_ret = _signature(func).return_annotation
        if len(keys) == 1:
            @_wraps(func)
            def wrapper(*args, **kwargs):
                return {keys[0]: func(*args, **kwargs)}
        elif isinstance(fun_ret, Iterable) and len(str(fun_ret)[12:].split(',')) == len(keys):
            @_wraps(func)
            def wrapper(*args, **kwargs) -> Dict[str, Union[str, _Real]]:
                data = {k: v for k, v in zip(keys, func(*args, **kwargs))}
                # data['ts'] = _dt.now().strftime(TS_PATTERN)
                return data
        else:
            raise ValueError('Keys mismatch to function returns annotation')
        return wrapper

    return _wrapper
