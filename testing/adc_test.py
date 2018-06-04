#! /usr/bin/env python3

import sys
from time import strftime, perf_counter, sleep
from collections import deque
from argparse import ArgumentParser

# import hardware interfaces
try:
    from Adafruit_ADS1x15 import ADS1115
    import RPi.GPIO as GPIO
except ImportError:
    print('failed to load hardware interfaces, using dummy for general checking')
    class ADS1115:
        @staticmethod
        def start_adc(channel, gain=1,data_rate=128):
            pass
        @staticmethod
        def stop_adc():
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

ADC_MAX_VOLTAGE = ADC_POLARITY * ADC_MAP[ADC_GAIN]
ADC_STEP_SIZE = abs(ADC_MAX_VOLTAGE / 2**16)  # volt/step

adc = ADS1115()

GPIO.setmode(GPIO.BCM)    # choose BCM or BOARD
# GPIO.setup(ADC_ALERT_PIN, GPIO.IN)
# GPIO.add_event_detect(ADC_ALERT_PIN, GPIO.RISING, adc_isr)

parser = ArgumentParser()
parser.add_argument('-c', '--channel', type=int, choices=(1,2,3,4), help='ADC input channel', default=ADC_CHANNEL)
parser.add_argument('-r', '--sample_rate', type=int, choices=(8, 16, 32, 64, 128, 250, 475, 860),
                                    default=ADC_SAMPLE_RATE, help='Sample rate for ADC')
parser.add_argument('-a','--alert_pin', type=int, default=ADC_ALERT_PIN, help='RPI gpio pin number (eg: gpio27 -> "-a 27")')
parser.add_argument('-p','--polarity', type=int, choices=(-1,+1), default=ADC_POLARITY, help='ADC input polarity (1, -1)')
parser.add_argument('-g','--gain', type=float, choices=(2/3,1,2,3,8,16), default=ADC_GAIN, help='ADC input polarity (1, -1)')
parser.add_argument('-V', '--version', action='version', version='%(prog)s {}'.format(__version__))

def adc_isr():
    global DATA, LAST_TIME
    ts = perf_counter()
    DATA.append((adc.get_last_result(), ts-LAST_TIME))
    LAST_TIME = ts

def main(alert_pin=21, channel=1, sample_rate=128, gain=1, polarity=1):
    max_voltage = polarity * ADC_MAP[gain]
    step_size = abs(max_voltage / ADC_LEVELS)
    GPIO.setup(alert_pin, GPIO.IN)
    GPIO.add_event_detect(alert_pin, GPIO.RISING, adc_isr)
    # start = perf_counter()
    adc.start_adc(channel, gain=gain, data_rate=sample_rate)
    sleep(5)
    # while perf_counter() - start < 5:
        # pass
    adc.stop_adc()

if __name__ == '__main__':
    args = vars(parser.parse_args())
    print(args)
    main(**args)
    print(DATA)
    print(len(DATA))
