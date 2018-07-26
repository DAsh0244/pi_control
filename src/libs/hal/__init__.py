"""
pi_control
__init__.py.py
Author: Danyal Ahsanullah
Date: 7/25/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: 
"""

from libs.utils import GPIO, SPI
from libs.hal.constants import PINS
from libs.hal.actuator import Actuator
from libs.hal.strain_gauge import StrainGauge
from libs.hal.thermocouple import Thermocouple
# noinspection PyPep8Naming
from libs.hal.adc import ADS1115Interface as A2D
# noinspection PyPep8Naming
from libs.hal.dac import MCP4725Interface as D2A
from libs.hal.sparkfun_openscale import OpenScale as LoadCell


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


# import hardware interfaces
# instantiate HW
adc = A2D(default_channel=1)
dac = D2A()
# todo: fix the soft/hard spi, configure naming ability.
t1 = Thermocouple(name='ambient', tc_type='T', num_avgs=4, hardware_spi=SPI.SpiDev(0, 0))  # SPI0, PORT0
t2 = Thermocouple(name='fluid', tc_type='T', num_avgs=4, hardware_spi=SPI.SpiDev(0, 1))  # SPI0, PORT1
t3 = Thermocouple(name='sample', tc_type='T', num_avgs=4, software_spi={'clk': 13, 'cs': 5, 'do': 19, 'di': 26})
# todo: fix configurability of strain gauge
s1 = StrainGauge(interface=adc)


# todo fix this so it works right
# load_cell = LoadCell(port=LOAD_CELL_PORT)


# noinspection PyMissingConstructor,PyPep8Naming
class load_cell(LoadCell):
    def __init__(self):
        pass

    def get_reading(self, **kwargs):
        from time import sleep
        from random import uniform
        sleep(uniform(100e-3, 700e-3))
        return 123, 456, 789


actuator = Actuator(position_sensor=adc, speed_controller=dac, force_sensor=load_cell())
