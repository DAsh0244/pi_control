#! /usr/bin/env python3

import sys
from collections import deque
from argparse import ArgumentParser
from time import strftime, perf_counter, sleep

# import hardware interfaces
try:
    from Adafruit_ADS1x15 import ADS1115
    from Adafruit_MCP4725 import MCP4725
    import RPi.GPIO as GPIO
except ImportError:
    print('failed to load hardware interfaces, using dummy for general checking')
    class MCP4725:
        @staticmethod
        def set_voltage(val):
            pass
    class ADS1115:
        @staticmethod
        def start_ADC(channel, gain=1,data_rate=128):
            pass
        @staticmethod
        def stop_ADC():
            pass
    class GPIO:
        BCM = IN = RISING = None
        @staticmethod
        def setmode(mode):
            pass
        @staticmethod
        def setup(pin, mode):
            pass
        @staticmethod
        def add_event_detect(pin, mode, callback):
            pass


__version_info = (0,0,1)
__version__ = '.'.join(map(str, __version_info))


DATA = deque()
LAST_TIME = 0
GLOBAL_VCC = 3.3

ADC_SAMPLE_BITS = 16
ADC_LEVELS = 2**ADC_SAMPLE_BITS
# ADS1115 PGA gain setting
# See table 3 in the ADS1015/ADS1115 datasheet for more info on gain.
ADC_MAP = {2/3 : 6.144,
                     1 : 4.096,
                     2 : 2.048,
                     4 : 1.024,
                     8 : 0.512,
                     16 : 0.256,
                    }

ADC_POLARITY = 1
ADC_GAIN = 1
ADC_CHANNEL = 1
ADC_ALERT_PIN = 21  # configurable
ADC_SAMPLE_RATE = 128  # 8, 16, 32, 64, 128, 250, 475, 860

ADC_MAX_VOLTAGE = min(ADC_POLARITY * ADC_MAP[ADC_GAIN] , GLOBAL_VCC)
ADC_STEP_SIZE = abs(ADC_MAX_VOLTAGE / 2**16)  # volt/step

ADC = ADS1115()

DAC_BITS = 12
DAC_LEVELS = 2**DAC_BITS
DAC_VOLTAGE = GLOBAL_VCC
DAC_STEP_SIZE = DAC_VOLTAGE/DAC_LEVELS


DAC = MCP4725()

GPIO.setmode(GPIO.BCM)    # choose BCM or BOARD
# GPIO.setup(ADC_ALERT_PIN, GPIO.IN)
# GPIO.add_event_detect(ADC_ALERT_PIN, GPIO.RISING, ADC_isr)

parser = ArgumentParser()
parser.add_argument('-c', '--channel', type=int, choices=(1,2,3,4), help='ADC input channel', default=ADC_CHANNEL)
parser.add_argument('-r', '--sample_rate', type=int, choices=(8, 16, 32, 64, 128, 250, 475, 860),
                                    default=ADC_SAMPLE_RATE, help='Sample rate for ADC')
parser.add_argument('-a','--alert_pin', type=int, default=ADC_ALERT_PIN, help='RPI gpio pin number (eg: gpio27 -> "-a 27")')
parser.add_argument('-p','--polarity', type=int, choices=(-1,+1), default=ADC_POLARITY, help='ADC input polarity (1, -1)')
parser.add_argument('-g','--gain', type=float, choices=(2/3,1,2,3,8,16), default=ADC_GAIN, help='ADC input polarity (1, -1)')
parser.add_argument('-t','--timeout', type=int, default=5, help='set timout for loop')
parser.add_argument('-V', '--version', action='version', version='%(prog)s {}'.format(__version__))

def diagnostic_adc_isr(channel):
    global DATA, LAST_TIME
    ts = perf_counter()
    DATA.append((ADC.get_last_result(), ts-LAST_TIME))
    LAST_TIME = ts

def calibrate_adc_isr(channel):
    pass


def moniter_adc_isr(channel):
    global LOG_FILE, LAST_TIME
    ts = perf_counter()
    LOG_FILE.write('{},{}\n'.format(ADC.get_last_result(), perf_counter()-start,value))
    LAST_TIME = ts
    if (value <= 750):  # ideally calibrate these
        print('17 on')
        GPIO.output(17, 1)
    elif (value >= 17800):
        print('17 off')
        GPIO.output(17, 0)

def test_adc(alert_pin=21, channel=1, sample_rate=128, gain=1, polarity=1, timeout=5):
    max_voltage = polarity * ADC_MAP[gain]
    step_size = abs(max_voltage / ADC_LEVELS)
    GPIO.setup(alert_pin, GPIO.IN)
    GPIO.add_event_detect(alert_pin, GPIO.BOTH, callback=diagnostic_adc_isr)  # may want to look into GPIO.RISING || GPIO.FALLING
    # start = perf_counter()
    print('starting loop')
    adc.start_adc_comparator(channel,2**16-1,0, gain=gain, data_rate=sample_rate)
    sleep(timeout)
    # while perf_counter() - start < 5:
        # pass
    adc.stop_adc()
    GPIO.cleanup()

def test_dac():
    pass

def calibrate_adc_thresholds():
    pass

def moniter_adc_file(outfile, timeout):
    GPIO.setup(ADC_ALERT_PIN, GPIO.IN)
    GPIO.add_event_detect(ADC_ALERT_PIN, GPIO.BOTH, callback=moniter_adc_isr)  # may want to look into GPIO.RISING || GPIO.FALLING
    adc.start_adc_comparator(channel,2**16-1,0, gain=gain, data_rate=sample_rate)
    sleep(timeout)
    adc.stop_adc()
    GPIO.cleanup()


if __name__ == '__main__':
    args = vars(parser.parse_args())
    print(args)
    test_adc(**args)
    print(DATA)
    print(len(DATA))
