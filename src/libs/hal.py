# hal.py
import numpy as np
from typing import Tuple, Union
from numbers import Real as _Real
from sys import platform as _platform
from collections import deque as _deque
from libs.utils import (
    nop as _nop,
    sop as _sop,
    in2mm
)
from libs.data_router import publish, add_to_periodic_poll
from libs.hal.max31856 import MAX31856
from libs.hal.sparkfun_openscale import OpenScale as LoadCell

# import hardware interfaces
try:
    import RPi.GPIO as GPIO
    import Adafruit_GPIO.SPI as SPI
except ImportError:
    import warnings as _warnings
    from time import sleep as _sleep
    from random import randint as _randint

    _warnings.warn('failed to load RPi.GPIO, using stub class for syntax checking', RuntimeWarning)
    _warnings.warn('failed to load Adafruit_GPIO, using stub class for syntax checking', RuntimeWarning)

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


    # noinspection PyUnusedLocal,PyPep8Naming
    class Adafruit_GPIO:
        """quick stub class for GPIO"""
        BCM = BOARD = IN = OUT = RISING = FALLING = BOTH = PUD_UP = PUD_DOWN = None
        setmode = setup = input = cleanup = add_event_detect = remove_event_detect = _nop
        HIGH = 1
        LOW = 0

        @staticmethod
        def output(channel, level):
            return _randint(0, 1)

        get_platform_gpio = _nop

        @staticmethod
        def wait_for_edge(channel, edge, timeout):
            _sleep(timeout // 1000)

        # provides hardware abstraction layer for easier access to hardware functions


    class SPI:
        MSBFIRST = 0

        class BitBang:
            def __init__(self, *args, **kwargs):
                pass

            set_clock_hz = set_mode = set_bit_order = transfer = _nop

        SpiDev = BitBang

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
        start_adc = start_adc_comparator = get_last_result = read_adc = read_adc_difference = _sop

# meta information
GLOBAL_VCC = 3.3
TIMEOUT = None
UNITS = 'raw'
OUTFILE = None
LOAD_CELL_PORT = 'COM10' if _platform == 'win32' else '/dev/ttyusb0'

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
    min_level = -1 * (levels >> 1)
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
        self.history: _deque = _deque(maxlen=history_len)
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
        converts a discrete level to a corresponding voltage value
        :type level: int
        :param level: raw reading from ADC converted to voltage
        :rtype: float
        :return: translated value
        """
        return level * self.step_size

    def voltage2level(self, voltage: float) -> int:
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
    stop = 0

    def __init__(self, vcc=GLOBAL_VCC, *args, history_len=20, **kwargs):
        self.value_history = _deque(maxlen=history_len)  # holds previous values
        self.value = 0  # holds current value
        self.vcc = vcc
        self.step_size = vcc / self.levels
        self.default_val = self.levels >> 1  # default is 1/2 speed
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
        converts a discrete level to a corresponding voltage value
        :type level: int
        :param level: discrete level to convert to voltage
        :rtype: float
        :return: translated value
        """
        return level * self.step_size

    def voltage2level(self, voltage: float) -> int:
        return round(voltage / self.step_size)


# alias abstractions ... will probably split these out and import with alias
A2D = _ADS1115
D2A = _MCP4725


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

    # todo: implement this
    def mount_controller(self, controller):
        pass

    def __init__(self, position_sensor: A2D, speed_controller: D2A, force_sensor: LoadCell,
                 pos_limits: dict = None, units: str = 'raw', movement_controller=None):
        """
        create an actuator interface
        :param position_sensor: ADC handle for position
        :param speed_controller: DAC handle for speed control
        :param force_sensor: ADC handle for measuring applied force
        :param pos_limits: dictionary of {'high':<int>, 'low':<int>} that enforce limits on positions
        :param units:
        """
        self.convert_units = {
            'raw': lambda level: level,
            'in': lambda level: level * self.distance_per_level,
            'mm': lambda level: in2mm(level * self.distance_per_level),
        }
        self.tolerance = 0.0001
        self.position_sensor = position_sensor
        self.speed_controller = speed_controller
        self.force_sensor = force_sensor
        self.distance_per_level = self.distance_per_volt * self.position_sensor.step_size
        self.pos_limit_low = 5000
        self.pos_limit_high = 26000
        self.units = units
        self.direction = 'forward'
        if pos_limits is not None:
            self.pos_limit_low = pos_limits.pop('low', self.pos_limit_low)
            self.pos_limit_high = pos_limits.pop('high', self.pos_limit_high)
        if movement_controller is not None:
            self.movement_controller = movement_controller
        add_to_periodic_poll(self._get_pos)
        add_to_periodic_poll(self._get_speed)
        add_to_periodic_poll(self._get_load)

    def _get_pos(self):
        return self.position

    def _get_speed(self):
        return self.speed

    def _get_load(self):
        return self.load

    @property
    @publish('actuator.position', ('pos_info',))
    def position(self) -> _Real:
        """
        gets position as the units value
        :return: raw integer representation of position
        """
        return self.convert_units[self.units](self.position_sensor.read_single())

    @property
    @publish('actuator.force', ('force', 'local_temp', 'timestamp'))
    def load(self) -> Tuple[float, float, int]:
        load = self.force_sensor.get_reading()
        return load

    @property
    @publish('actuator.speed', ('speed',))
    def speed(self):
        return self.speed_controller.value

    @speed.setter
    def speed(self, value):
        self.speed_controller.set_level(value)

    def set_actuator_dir(self, direction: Union[str, None] = None) -> None:
        """
        sets actuator direction as forward or backward. If direction is not passed, the current direction is flipped.
        :type direction: str or None
        :param direction: string describing direction. Either '(f)orward' or '(b)ackward'
        :return: None
        """
        if direction is None:
            # noinspection PyCallByClass
            GPIO.output(PINS['relay_1'], not GPIO.input(PINS['relay_1']))
            self.direction = 'forward' if self.direction != 'forward' else 'backward'
        if direction in {'forward', 'f'}:
            GPIO.output(PINS['relay_1'], GPIO.HIGH)
            self.direction = 'forward'
        elif direction in {'backward', 'b'}:
            GPIO.output(PINS['relay_1'], GPIO.LOW)
            self.direction = 'backward'
        else:
            raise ValueError('unknown direction {!r}'.format(direction))

    # will require speed vs voltage information
    # todo: get data for speed vs voltage info
    # https://github.com/an-oreo/pi_control/issues/9
    def set_out_speed(self, speed) -> None:
        self.speed_controller.set_level(speed)
        return None
        # raise NotImplementedError('no information known for this')

    def set_position(self, position: Union[float, int]) -> None:
        """
        sets actuator to provided position. if overshoot is detected, attempts to correct.
        :param position: position value like those obtained from self.position
        :return: None
        """
        eps = position * self.tolerance
        # value = self.position_sensor.read_single()
        positions = _deque(maxlen=2)
        positions.append(self.position)
        value = sum(positions) / positions.maxlen
        # print(value)
        if abs(value - position) < eps:
            print(f'target achieved\ndesired: {position}\nachieved: {value}\nerror: {position - value}')
            return None
        if value >= position:
            self.set_actuator_dir('backward')
        else:  # value < position
            self.set_actuator_dir('forward')
        self.speed_controller.set_level(self.speed_controller.default_val)
        while True:
            # self.position_sensor.wait_for_sample()
            # value = self.position_sensor.get_last_result()
            # value = self.position_sensor.read_single()
            positions.append(self.position)
            value = sum(positions) / positions.maxlen
            print(self.speed_controller.value, value)
            if (self.speed_controller.value == self.speed_controller.stop) \
                    or abs(value - position) < eps:
                print('target achieved')
                print('desired', position)
                print('achieved', value)
                print('error', position - value)
                # self.position_sensor.stop_adc()
                return
            elif value > position and self.direction != 'backward':  # too far, go back
                self.set_actuator_dir('backward')
            elif value < position and self.direction != 'forward':  # not far enough, go forward
                self.set_actuator_dir('forward')

    def level2position(self, level: int, units: str = 'in') -> float:
        """
        converts a integer level to a position value
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


class Thermocouple(MAX31856):

    def __init__(self, name: str, tc_type, num_avgs, *args, **kwargs):
        super().__init__(tc_type=tc_type, avgsel=num_avgs, *args, **kwargs)
        self._tc_type_str = tc_type
        self._avg_samples = num_avgs
        self.name = name
        add_to_periodic_poll(self.get_temps)

    def read_temp(self):
        return super().read_temp_c()

    def read_internal_temp(self):
        return super().read_internal_temp_c()

    @publish('thermocouple', ('meta', 'temp', 'internal_temp'))
    def get_temps(self) -> Tuple[str, float, float]:
        return self.name, self.read_temp(), self.read_internal_temp()

    @property
    def fault_register(self):
        return super().read_fault_register()

    @property
    def thermocouple_type(self):
        return self._tc_type_str

    @thermocouple_type.setter
    def thermocouple_type(self, value):
        self._tc_type_str = value
        self.tc_type = self.THERMOCOUPLE_MAP[value]
        cr1 = ((self.avgsel << 4) + self.tc_type)
        self._write_register(self.MAX31856_REG_WRITE_CR1, cr1)

    @property
    def averaging_samples(self):
        return self._avg_samples

    @averaging_samples.setter
    def averaging_samples(self, value):
        self._avg_samples = value
        self.avgsel = self.SAMPLE_MAP[value]
        cr1 = ((self.avgsel << 4) + self.tc_type)
        self._write_register(self.MAX31856_REG_WRITE_CR1, cr1)


class StrainGauge:
    def __init__(self, interface: A2D, vcc: float = 5.0, gf: float = 2.0, r_nom: float = 350.0):
        self.interface = interface
        self.vcc = vcc
        self.gf = gf
        self.r_nom = r_nom
        self.cal_map = np.array([[], []])
        add_to_periodic_poll(self.read_strain)

    @publish('strain', ('strain',))
    def read_strain(self):
        raw = self.interface.read_adc_difference(3, gain=4, data_rate=860)
        voltage = self.interface.level2voltage(raw) + (self.vcc / 2)
        strain = (1 / voltage - 1) / self.gf
        return strain

    @publish('strain', ('strain',))
    def read_adjusted_strain(self):
        """
        tries applying a linear piecewise interpolated to the read strain value as a correction factor.
        :return:
        """
        strain = self.read_strain()
        correction = np.interp(strain, self.cal_map[:, 0], self.cal_map[:, 1])
        return strain + correction

    def add_cal_point(self, target):
        """
        Call after the system is strained to a known strain value
        successive calls with differing strain targets help form a better curve

        recommendation is to call multiple times at various strains.
        """
        strain = self.read_strain()
        diff = (target - strain)
        self.cal_map = np.vstack((self.cal_map, [target, diff]))


# instantiate HW
adc = A2D(default_channel=1)
dac = D2A()


# noinspection PyMissingConstructor,PyPep8Naming
class __load_cell(LoadCell):
    def __init__(self):
        pass

    def get_reading(self, **kwargs):
        from time import sleep
        from random import uniform
        sleep(uniform(100e-3, 700e-3))
        return 123, 456, 789


load_cell = __load_cell()
# load_cell = LoadCell(port=LOAD_CELL_PORT)
actuator = Actuator(position_sensor=adc, speed_controller=dac, force_sensor=load_cell)
# todo: fix the soft/hard spi, configure naming ability.
SPI_PORT = 0
SPI_DEVICE = 0
t1 = Thermocouple(name='ambient', tc_type='T', num_avgs=4, hardware_spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))

SPI_PORT = 0
SPI_DEVICE = 1
t2 = Thermocouple(name='fluid', tc_type='T', num_avgs=4, hardware_spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))
t3 = Thermocouple(name='sample', tc_type='T', num_avgs=4, software_spi={'clk': 13, 'cs': 5, 'do': 19, 'di': 26})
# todo: fix configurability of strain gauge
s1 = StrainGauge(interface=adc)


# noinspection PyCallByClass
def hal_init():
    # choose BCM or BOARD
    GPIO.setmode(GPIO.BCM)
    # setup pins
    # GPIO.setup(PINS['adc_alert'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(PINS['relay_1'], GPIO.OUT)  # set GPIO17 as an output
    GPIO.setup(PINS['relay_2'], GPIO.OUT)  # set GPIO22 as an output
    # initialize output values
    GPIO.output(PINS['relay_2'], GPIO.LOW)  # set GPIO22 to 0/GPIO.LOW/False
    GPIO.output(PINS['relay_1'], GPIO.LOW)  # set GPIO22 to 0/GPIO.LOW/False
    dac.set_level(dac.stop)


def hal_cleanup():
    dac.set_voltage(dac.stop)
    adc.stop_adc()
    GPIO.cleanup()


if __name__ == '__main__':
    from libs.data_router import DataLogger

    CONFIG = {
        'length_units': 'mm',
        'force_units': 'N',
    }

    Thermocouple.read_temp = lambda *args: 1.23456789
    Thermocouple.read_internal_temp = lambda *args: 3.14159265358979323846264338
    t1 = Thermocouple(name='ambient', tc_type='T', num_avgs=1, software_spi={'clk': 1, 'cs': 2, 'do': 3, 'di': 4})
    t2 = Thermocouple(name='fluid', tc_type='T', num_avgs=1, software_spi={'clk': 1, 'cs': 2, 'do': 3, 'di': 4})
    t3 = Thermocouple(name='sample', tc_type='T', num_avgs=1, software_spi={'clk': 1, 'cs': 2, 'do': 3, 'di': 4})
    logger = DataLogger(config=CONFIG)
    for i in range(1, 10):
        print(t1.get_temps())
        print(t2.get_temps())
        print(t3.get_temps())
