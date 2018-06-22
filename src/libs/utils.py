# util.py
# utility misc functions

# noinspection PyUnresolvedReferences
import warnings as _warnings
from random import randint as _randint
# noinspection PyUnresolvedReferences
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
