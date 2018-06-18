# hal.py
from libs.utils import (
    nop as _nop,
    sop as _sop,
    in2mm
)
from collections import deque as _deque


# import hardware interfaces
try:
    import RPi.GPIO as GPIO
except ImportError:
    import warnings as _warnings
    from time import sleep as _sleep
    from random import randint as _randint
    _warnings.warn('failed to load RPi.GPIO, using stub class for syntax checking', RuntimeWarning)


    # noinspection PyUnusedLocal
    class GPIO:
        """quick stub class for GPIO"""
        BCM = BOARD = IN = OUT = RISING = FALLING = BOTH = PUD_UP = PUD_DOWN = None
        setmode = setup = input = cleanup = add_event_detect = remove_event_detect = _nop
        HIGH = 1
        LOW = 0

        @staticmethod
        def output(channel, level):
            return _randint(0, 1)

        @staticmethod
        def wait_for_edge(channel, edge, timeout):
            _sleep(timeout // 1000)
    # provides hardware abstraction layer for easier access to hardware functions

try:
    from Adafruit_ADS1x15 import ADS1115
    from Adafruit_MCP4725 import MCP4725
except ImportError:
    import warnings as _warnings
    _warnings.warn('failed to load hardware interfaces for ADC and/or DAC, using stub classes for syntax checking',
                   RuntimeWarning)


    class MCP4725:
        """quick stub class for mcp4725"""
        set_voltage = _nop


    class ADS1115:
        """quick stub class for ADS1115"""
        stop_adc = _nop
        start_adc = start_adc_comparator = get_last_result = read_adc = _sop

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

    def __init__(self, sample_rate=128, gain=1, vcc=GLOBAL_VCC, default_channel=0,
                 *extra, alert_pin=21, history_len=20):
        self.vcc = vcc
        self.sample_rate = sample_rate
        self.gain = gain
        self.default_channel = default_channel
        self.alert_pin = alert_pin
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
        return self.start_adc_comparator(self.default_channel, 2 ** 16 - 1, 0, gain=self.gain,
                                         data_rate=self.sample_rate)

    def wait_for_sample(self, timeout=2):
        """
        blocking call to wait for the ADC's Alert pin to signal conversion ready
        :return: None
        """
        GPIO.wait_for_edge(self.alert_pin, GPIO.FALLING, timeout=timeout)

    def level2voltage(self, level):
        return level * self.step_size


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

    def set_level(self, level):
        self.value_history.append(self.value)
        self.value = level
        super().set_voltage(self.value)

    def set_voltage(self, voltage):
        self.value_history.append(self.value)
        self.value = round(voltage / self.step_size)
        super().set_voltage(self.value)

        # noinspection SpellCheckingInspection


# instantiate HW
ADC = A2D(default_channel=1)
DAC = _DAC()


# setup wrapper for actuator
class Actuator:
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

    def __init__(self, position_sensor, speed_controller, force_sensor):
        self.position_sensor = position_sensor
        self.speed_controller = speed_controller
        self.force_sensor = force_sensor
        self.pos = self.get_position()
        self.load = self.get_load()

    def get_position(self):
        return self.distance_per_level * self.position_sensor.get_last_result()

    def get_load(self):
        return 4  # guaranteed random todo: work on implementing this

    @staticmethod
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

    def set_out_speed(self, speed):
        pass
        # will require speed vs voltage information

    def level2position(self, level, units='in'):
        """
        :param level:
        :param units: either 'in' or 'mm', returns in proper distance
        :return:
        """
        pos = level * self.distance_per_level  # returns in inches
        if units == 'mm':
            return in2mm(pos)
        else:
            return pos

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


def hal_cleanup():
    DAC.set_voltage(DAC.stop)
    ADC.stop_adc()
    GPIO.cleanup()


def set_config():
    return None


def load_config(config):
    pass


def register_routine():
    return None


def register_action():
    return None
