# hal.py
from collections import deque as _deque

from libs.utils import (
    nop as _nop,
    sop as _sop,
    in2mm
)

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

    _warnings.warn('failed to load hardware interfaces for adc and/or dac, using stub classes for syntax checking',
                   RuntimeWarning)


    class MCP4725:
        """quick stub class for mcp4725"""
        set_voltage = _nop


    class ADS1115:
        """quick stub class for ADS1115"""
        stop_adc = _nop
        start_adc = start_adc_comparator = get_last_result = read_adc = _sop

# meta information
GLOBAL_VCC = 3.3
TIMEOUT = None
UNITS = 'raw'
OUTFILE = None

# pin mappings
PINS = {
    'relay_1': 17,
    'relay_2': 22,
    'adc_alert': 21,
}


class _ADS1115(ADS1115):
    """
    Extended ADS1115 interface with builtin convenience for configuration and reading
    """
    bits = 16
    levels = 1 << bits
    max_level = (levels >> 1) - 1
    min_level = levels >> 1
    pga_map = {2 / 3: 6.144,  # map of gain values vs max peak readable voltage
               1: 4.096,
               2: 2.048,
               4: 1.024,
               8: 0.512,
               16: 0.256,
               }
    accepted_sample_rates = {8, 16, 32, 64, 128, 250, 475, 860}
    accepted_gains = {2 / 3, 1, 2, 4, 8, 16}
    accepted_channels = {0, 1, 2, 3}

    def __init__(self, sample_rate: int = 128, gain: int = 1, vcc: float = GLOBAL_VCC, default_channel: int = 0,
                 alert_pin: int = 21, history_len: int = 20):
        """
        initialize the ADS1115 interface
        :type history_len: int
        :type alert_pin: int
        :type vcc: float
        :type default_channel: int
        :type gain: int
        :type sample_rate: int
        :param sample_rate: Sample rate (samples/sec) as an integer. Must be within: {8, 16, 32, 64, 128, 250, 475, 860}
        :param gain: Internal PGA gain, accepted values are: {2 / 3, 1, 2, 4, 8, 16}
        :param vcc: Supply voltage (V) usually 3.3 or 5
        :param default_channel: default input channel. Must be within {0, 1, 2, 3}
        :param alert_pin: Pin the ADC ALRT/RDY pin is tied to.
        :param history_len: how many previous values to keep. If value is exceeded, the oldest value is dropped.
        """
        self.vcc = vcc
        self.sample_rate = sample_rate
        self.gain = gain
        self.default_channel = default_channel
        self.alert_pin = alert_pin
        self.step_size = 2 * self.max_voltage / self.levels
        self.history = _deque(maxlen=history_len)
        super().__init__()

    def get_last_result(self):
        """
        returns contents of read register for device.
        Adds value to history
        :return: integer representing the voltage level
        """
        res = super().get_last_result()
        self.history.append(res)
        return res

    @property
    def max_voltage(self) -> float:
        """
        returns max readable voltage
        :rtype: float
        :return: max input voltage level (+/-) or supply if limited to that
        """
        return min(self.pga_map[self.gain], self.vcc)

    def start_conversions(self) -> int:
        """
        starts conversions with preset defaults
        :rtype: int
        :return: first reading from ADC
        """
        return self.start_adc_comparator(self.default_channel, self.max_level, self.min_level, gain=self.gain,
                                         data_rate=self.sample_rate)

    def wait_for_sample(self, timeout=2):
        """
        blocking call to wait for the adc's Alert pin to signal conversion ready
        :return: None
        """
        GPIO.wait_for_edge(self.alert_pin, GPIO.FALLING, timeout=timeout)

    def read_single(self) -> int:
        """
        reads a single-shot reading from the ADC
        :rtype: int
        :return: reading from ADC single shot reading
        """
        return self.read_adc(self.default_channel, gain=self.gain, data_rate=self.sample_rate)

    def level2voltage(self, level: int) -> float:
        """

        :type level: int
        :param level: raw reading from ADC converted to voltage
        :rtype: float
        :return: translated value
        """
        return level * self.step_size

    def voltage2level(self, voltage: float) -> int:  # todo: check if round or int division
        return round(voltage / self.step_size)

    def stop(self):
        super().stop_adc()


# dac wrapper
class _MCP4725(MCP4725):
    """
    MCP4725 wrapper with added convenience functionality
    """
    bits = 12
    levels = 1 << bits
    vcc = GLOBAL_VCC
    step_size = vcc / levels
    default_val = levels >> 2  # default is 1/4 speed
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
        self.value = self.voltage2level(voltage)
        super().set_voltage(self.value)

    def level2voltage(self, level: int) -> float:
        """

        :type level: int
        :param level: raw reading from ADC converted to voltage
        :rtype: float
        :return: translated value
        """
        return level * self.step_size

    def voltage2level(self, voltage: float) -> int:  # todo: check if round or int division
        return round(voltage / self.step_size)


# setup wrapper for actuator
class Actuator:
    """
    Actuator interface for main drive arm
    """
    stroke = 12  # stroke length (inches)
    pot_value = 10000  # 10k pot
    pot_voltage = GLOBAL_VCC  # connected to a 3v3 supply rail
    inches_per_second = {35: {'none': 2.00, 'full': 1.38},
                         50: {'none': 1.14, 'full': 0.83},
                         150: {'none': 0.37, 'full': 0.28},
                         }  # key is force (lbs)
    distance_per_volt = stroke / pot_voltage

    def __init__(self, position_sensor, speed_controller, force_sensor, pos_limits: dict = None, units: str = 'raw',
                 movement_controller=None):
        """
        create an actuator interface
        :param position_sensor: ADC handle for position
        :param speed_controller: DAC handle for speed control
        :param force_sensor: ADC handle for measuring applied force
        :param pos_limits: dictionary of {'high':<int>, 'low':<int>} that enforce limits on positions
        :param units:
        """
        self.position_sensor = position_sensor
        self.speed_controller = speed_controller
        self.force_sensor = force_sensor
        self.distance_per_level = self.distance_per_volt * self.position_sensor.step_size
        self.pos_limit_low = 5000
        self.pos_limit_high = 26000
        self.units = units
        if pos_limits is not None:
            self.pos_limit_low = pos_limits.pop('low', self.pos_limit_low)
            self.pos_limit_high = pos_limits.pop('high', self.pos_limit_high)
        if movement_controller is not None:
            self.movement_controller = movement_controller

    @property
    def position(self) -> int:
        """
        gets position as raw value
        :return: raw integer representation of position
        """
        return self.position_sensor.read_single()

    @property
    def load(self) -> int:
        load = self.force_sensor.get_last_result()
        return load  # guaranteed random todo: work on implementing this

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

    def set_out_speed(self, speed) -> None:
        pass
        # will require speed vs voltage information

    def set_position(self, position: int) -> None:
        """
        sets actuator to provided position.
        :type position: int
        :param position: raw position value like those obtained form self.position
        :return: None
        """
        value = self.position_sensor.start_conversions()
        print(value)
        if value == position:
            return None
        if value >= position:
            self.set_actuator_dir('backward')
        else:  # value < position
            self.set_actuator_dir('forward')
        self.speed_controller.set_level(self.speed_controller.default_val)
        passed = False
        while True:
            self.position_sensor.wait_for_sample()
            value = self.position_sensor.get_last_result()
            print(self.speed_controller.value, value)
            if self.speed_controller.value == self.speed_controller.stop:
                print('target achieved')
                print('desired', position)
                print('achieved', value)
                print('error', position - value)
                self.position_sensor.stop_adc()
                break
            elif value >= position:  # too far, go back
                self.set_actuator_dir('backward')
                if passed:
                    self.speed_controller.set_level(self.speed_controller.value >> 1)
                    passed = False
                else:
                    print('passed high target')
                    passed = True
            else:  # not far enough, go forward
                self.set_actuator_dir('forward')
                if passed:
                    self.speed_controller.set_level(self.speed_controller.value >> 1)
                    passed = False
                else:
                    print('passed low target')
                    passed = True

    def level2position(self, level: int, units: str = 'in') -> float:
        """
        converts a integer level to a position value
        :type units: str
        :type level: int
        :param level: integer level like one obtained form self.position
        :param units: str
        :return: float of newly converted units
        """
        pos = level * self.distance_per_level  # returns in inches
        if units == 'mm':
            return in2mm(pos)
        else:
            return pos

    def reset_max(self):
        self.set_position(self.pos_limit_high)

    def reset_min(self):
        self.set_position(self.pos_limit_low)


# instantiate HW
adc = _ADS1115(default_channel=1)
dac = _MCP4725()
actuator = Actuator(position_sensor=adc, speed_controller=dac, force_sensor=None)


# noinspection PyCallByClass
def hal_init():
    # choose BCM or BOARD
    GPIO.setmode(GPIO.BCM)
    # setup pins
    GPIO.setup(PINS['adc_alert'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(PINS['relay_1'], GPIO.OUT)  # set GPIO17 as an output
    GPIO.setup(PINS['relay_2'], GPIO.OUT)  # set GPIO22 as an output
    # initialize output values
    GPIO.output(PINS['relay_2'], 0)  # set GPIO22 to 0/GPIO.LOW/False
    GPIO.output(PINS['relay_1'], 0)  # set GPIO22 to 0/GPIO.LOW/False
    dac.set_level(dac.stop)


def hal_cleanup():
    dac.set_voltage(dac.stop)
    adc.stop_adc()
    GPIO.cleanup()


def set_config():
    return None


# noinspection PyUnusedLocal
def load_config(config):
    pass
