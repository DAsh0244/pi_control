# hal.py
# put pin configurations and such here
#
# usage:

from collections import deque as _deque
from random import randint as _randint


def _nop(*args, **kwargs):
    """function that matches any prototype and proceeds to do nothing"""
    pass


# noinspection PyUnusedLocal
def _sop(*args, **kwargs):
    """function that matches any prototype and just returns a random int"""
    return _randint(0, 2 ** 15 - 1)


# noinspection PyUnusedLocal
def _warning_on_one_line(message, category, filename, lineno, file=None, line=None):
    return '%s:%s: %s: %s\n\n' % (filename, lineno, category.__name__, message)


# import hardware interfaces
try:
    import RPi.GPIO as GPIO
except ImportError:
    import warnings as _warnings

    _warnings.formatwarning = _warning_on_one_line
    _warnings.warn('failed to load RPi.GPIO, using stub class for syntax checking', RuntimeWarning)


    class GPIO:
        """quick stub class for GPIO"""
        BCM = BOARD = HIGH = LOW = IN = OUT = RISING = FALLING = BOTH = PUD_UP = PUD_DOWN = None
        setmode = setup = add_event_detect = cleanup = remove_event_detect = output = input = wait_for_edge = _nop
    # provides hardware abstraction layer for easier access to hardware functions

try:
    from Adafruit_ADS1x15 import ADS1115
    from Adafruit_MCP4725 import MCP4725
except ImportError:
    import warnings as _warnings

    _warnings.formatwarning = _warning_on_one_line
    _warnings.warn('failed to load hardware interfaces for ADC and/or DAC, using stub classes for syntax checking',
                   RuntimeWarning)


    class MCP4725:
        """quick stub class for mcp4725"""
        set_voltage = _nop


    class ADS1115:
        """quick stub class for ADS1115"""
        start_adc = start_adc_comparator = stop_adc = get_last_result = read_adc = _sop
# from hal import *

# meta information that may be useful
GLOBAL_VCC = 3.3
TIMEOUT = None
UNITS = 'raw'
OUTFILE = None

# Pins
PINS = {
    'relay_1': 17,
    'relay_2': 22,
    'adc_alert': 21,
}


class A2D(ADS1115):
    bits = 16
    levels = 2 ** bits
    pga_map = {2 / 3: 6.144,  # map of gain values vs max peak readable voltage
               1: 4.096,
               2: 2.048,
               4: 1.024,
               8: 0.512,
               16: 0.256,
               }

    def __init__(self, sample_rate=128, gain=1, vcc=GLOBAL_VCC, default_channel=0, *extra, history_len=20):
        self.vcc = vcc
        self.sample_rate = sample_rate
        self.gain = gain
        self.default_channel = default_channel
        self.step_size = 2 * self.max_voltage / self.levels
        self.history = _deque(maxlen=history_len)
        super().__init__()

    def get_last_result(self):
        res = super().get_last_result()
        self.history.append(res)
        return res

    @property
    def max_voltage(self):
        return self.pga_map[self.gain]

    def start_conversions(self):
        self.start_adc_comparator(self.default_channel, 2 ** 16 - 1, 0, gain=self.gain, data_rate=self.sample_rate)


# noinspection PyUnusedLocal


# instantiate ADC
ADC = A2D(default_channel=1)


# ADC = ADS1115()


class ActuatorConfig:
    pos_limit_low = 10
    pos_limit_high = 26000
    pos_threshold_high = 17800
    pos_threshold_low = 750
    stroke = 12  # stroke length (inches)
    pot_value = 10000  # 10k pot
    pot_voltage = GLOBAL_VCC  # connected to a 3v3 supply rail
    actuator_inches_per_second = {35: {'none': 2.00, 'full': 1.38},
                                  50: {'none': 1.14, 'full': 0.83},
                                  150: {'none': 0.37, 'full': 0.28},
                                  }  # key is force (lbs)
    distance_per_volt = stroke / pot_voltage
    distance_per_level = distance_per_volt * ADC.step_size


# DAC wrapper
class _DAC(MCP4725):
    bits = 12
    levels = 2 ** bits
    vcc = GLOBAL_VCC
    step_size = vcc / levels
    default_val = 1024
    stop = 0

    def __init__(self, *args, history_len=20, **kwargs):
        self.value_history = _deque(maxlen=history_len)  # holds previous values
        self.value = 0  # holds current value
        super().__init__(*args, **kwargs)

    def set_voltage(self, level):
        self.value_history.append(self.value)
        self.value = level
        super().set_voltage(level)

    # noinspection SpellCheckingInspection
    def set_vout(self, vout):
        self.value_history.append(self.value)
        self.value = vout / self.vcc * self.levels
        super().set_voltage(self.value)

    def set_out_speed(self, speed):
        pass
        # will require speed vs voltage information


# DAC = MCP4725()
DAC = _DAC()


# hardware actions
# class HwAction:
#     def __init__(self, name, action):
#         self.name = name
#         self.action = action
#
#     def do(self):
#         self.action()

# noinspection PyCallByClass
def hal_init():
    # choose BCM or BOARD
    GPIO.setmode(GPIO.BCM)
    # setup pins
    GPIO.setup(PINS['adc_alert'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(PINS['relay_1'], GPIO.OUT)  # set GPIO17 as an output
    GPIO.setup(PINS['relay_2'], GPIO.OUT)  # set GPIO22 as an output


# noinspection PyCallByClass
def wait_for_sample():
    """
    blocking call to wait for the ADC's Alert pin to signal conversion ready
    :return: None
    """
    GPIO.wait_for_edge(PINS['adc_alert'], GPIO.FALLING)


# noinspection PyCallByClass
def set_actuator_dir(direction: str) -> None:
    """
    sets actuator direction as forward or backward
    :type direction: str
    :param direction: string describing direction. Either '(f)orward' or '(b)ackward'
    :return: None
    """
    if direction in {'forward', 'f'}:
        GPIO.output(PINS['relay_1'], GPIO.HIGH)
    elif direction in {'backward', 'b'}:
        GPIO.output(PINS['relay_1'], GPIO.LOW)
    else:
        raise ValueError('unknown direction {!r}'.format(direction))


def load_config(config):
    pass
