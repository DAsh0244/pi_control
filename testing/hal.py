# hal.py
# provides hardware abstraction layer for easier access to hardware functions
# put pin configurations and such here
#
# usage:
# from hal import *

from collections import deque as _deque
from random import randint as _randint


# noinspection PyUnusedLocal
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

# meta information that may be useful
GLOBAL_VCC = 3.3
TIMEOUT = None
UNITS = 'raw'
OUTFILE = None

# Pins
RELAY_1_PIN = 17
RELAY_2_PIN = 22
ADC_ALERT_PIN = 21

# DAC info
DAC_BITS = 12
DAC_LEVELS = 2 ** DAC_BITS
DAC_VOLTAGE = GLOBAL_VCC
DAC_STEP_SIZE = DAC_VOLTAGE / DAC_LEVELS
DEFAULT_DAC_VAL = 1024
DAC_VAL = DEFAULT_DAC_VAL


# potential DAC wrapper
class _DAC(MCP4725):
    bits = 12
    levels = 2 ** bits
    vcc = GLOBAL_VCC
    step_size = vcc / levels
    default_val = 1024

    def __init__(self, *args, **kwargs):
        self.value_history = _deque(maxlen=10)  # holds previous values
        self.dac_value = 0  # holds current value
        super().__init__(*args, **kwargs)

    # noinspection SpellCheckingInspection
    def set_vout(self, vout):
        self.value_history.append(self.dac_value)
        self.dac_value = vout / self.vcc * self.levels
        self.set_voltage(self.dac_value)

    def set_out_speed(self, speed):
        # will require speed vs voltage information
        pass


# ADC info
ADC_GAIN = 1  # configurable, value must be one of: 2/3, 1, 2, 4, 8, 16
ADC_CHANNEL = 1  # configurable, value must be one of: 0, 1, 2, 3
ADC_SAMPLE_RATE = 128  # configurable, value must be: 8, 16, 32, 64, 128, 250, 475, 860
ADC_SAMPLE_BITS = 16
ADC_LEVELS = 2 ** ADC_SAMPLE_BITS
ADC_PGA_MAP = {2 / 3: 6.144,
               1: 4.096,
               2: 2.048,
               4: 1.024,
               8: 0.512,
               16: 0.256,
               }
ADC_MAX_VOLTAGE = ADC_PGA_MAP[ADC_GAIN]
ADC_STEP_SIZE = 2 * ADC_MAX_VOLTAGE / (2 ** 16)  # volt/step
ADC_MAX_LEVEL = 2 ** 16 / 2 - 1  # hits ADC_MAX_VOLTAGE

# Actuator information
STROKE = 12  # stroke length (INCHES)
POT_VALUE = 10000  # 10k pot
POT_VOLTAGE = 3.3  # connected to a 3V3 supply rail
DISTANCE_PER_VOLT = STROKE / POT_VOLTAGE
ACTUATOR_INCHES_PER_SECOND = {35: {'None': 2.00, 'Full': 1.38},
                              50: {'None': 1.14, 'Full': 0.83},
                              150: {'None': 0.37, 'Full': 0.28},
                              }  # key is force (lbs)
DISTANCE_PER_LEVEL = ADC_STEP_SIZE * DISTANCE_PER_VOLT  # inches / step

# default Thresholds
POS_LIMIT_LOW = 10
POS_THRESHOLD_LOW = 750
POS_THRESHOLD_HIGH = 17800
POS_LIMIT_HIGH = round(GLOBAL_VCC / ADC_MAX_VOLTAGE * ADC_MAX_LEVEL)


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

    def __init__(self, sample_rate=128, gain=1, vcc=GLOBAL_VCC, default_channel=0):
        self.vcc = vcc
        self.sample_rate = sample_rate
        self.gain = gain
        self.default_channel = default_channel
        self.step_size = 2 * self.max_voltage / self.levels
        super().__init__()

    @property
    def max_voltage(self):
        return self.pga_map[self.gain]

    def start_conversions(self):
        self.start_adc_comparator(self.default_channel, 2 ** 16 - 1, 0, gain=self.gain, data_rate=self.sample_rate)


# HW abstractions
DAC = MCP4725()
ADC = A2D(default_channel=1)


# ADC = ADS1115()


class ActuatorConfig:
    pos_limit_low = 10
    pos_limit_high = round(GLOBAL_VCC / ADC_MAX_VOLTAGE * ADC_MAX_LEVEL)
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


# noinspection PyCallByClass
def hal_init():
    # choose BCM or BOARD
    GPIO.setmode(GPIO.BCM)
    # setup pins
    GPIO.setup(ADC_ALERT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(RELAY_1_PIN, GPIO.OUT)  # set GPIO17 as an output
    GPIO.setup(RELAY_2_PIN, GPIO.OUT)  # set GPIO22 as an output


# noinspection PyCallByClass
def wait_for_sample():
    """
    blocking call to wait for the ADC's Alert pin to signal conversion ready
    :return: None
    """
    GPIO.wait_for_edge(ADC_ALERT_PIN, GPIO.FALLING)


# noinspection PyCallByClass
def set_actuator_dir(direction: str) -> None:
    """
    sets actuator direction as forward or backward
    :type direction: str
    :param direction: string describing direction. Either '(f)orward' or '(b)ackward'
    :return: None
    """
    if direction in {'forward', 'f'}:
        GPIO.output(RELAY_1_PIN, GPIO.HIGH)
    elif direction in {'backward', 'b'}:
        GPIO.output(RELAY_1_PIN, GPIO.LOW)
    else:
        raise ValueError('unknown direction {!r}'.format(direction))


def load_config(config):
    pass
