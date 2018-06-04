#! /usr/bin/env python3

import sys
import json
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

def adc_level_to_voltage(level):
    return level * ADC_STEP_SIZE

def get_position(stroke, level):
    pass

ADC = ADS1115()

DAC_BITS = 12
DAC_LEVELS = 2**DAC_BITS
DAC_VOLTAGE = GLOBAL_VCC
DAC_STEP_SIZE = DAC_VOLTAGE/DAC_LEVELS


DAC = MCP4725()

POS_THREHSOLD_LOW = 750
POS_THREHSOLD_HIGH = 17800

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
parser.add_argument('-s','--save', type=str, default=None, help='optional file to save results to')
parser.add_argument('--config', type=str, default=None, help='optional configuration file')


parser.add_argument('-V', '--version', action='version', version='%(prog)s {}'.format(__version__))

def diagnostic_adc_isr(channel):
    global DATA, LAST_TIME
    ts = perf_counter()
    DATA.append((ADC.get_last_result(), ts-LAST_TIME))
    LAST_TIME = ts

def calibrate_adc_isr(channel):
    pass


def moniter_adc_isr(channel):
    global LOGFILE, LAST_TIME
    ts = perf_counter()
    value = ADC.get_last_result()
    LOGFILE.write('{},{}\n'.format(value,ts-LAST_TIME))
    LAST_TIME = ts
    """
    starts at stop:
    value ~ 0
        gpio on:
    value < 750
        gpio on:
    750 < value < 17800
        gpio on:
    value > 17800
        gpio off
    """

    if value >= POS_THREHSOLD_HIGH or value < 5:
        print('17 off')
        GPIO.output(17, 0)
    else:
        print('17 on')
        GPIO.output(17, 1)


def test_adc(alert_pin=21, channel=1, sample_rate=128, gain=1, polarity=1, timeout=5, *args, **kwargs):
    max_voltage = polarity * ADC_MAP[gain]
    step_size = abs(max_voltage / ADC_LEVELS)
    GPIO.setup(alert_pin, GPIO.IN)
    GPIO.add_event_detect(alert_pin, GPIO.BOTH, callback=diagnostic_adc_isr)  # may want to look into GPIO.RISING || GPIO.FALLING
    # start = perf_counter()
    print('starting loop')
    LAST_TIME=perf_counter()
    ADC.start_adc_comparator(channel,2**16-1,0, gain=gain, data_rate=sample_rate)
    sleep(timeout)
    # while perf_counter() - start < 5:
        # pass
    ADC.stop_adc()

def test_dac():
    pass

# def calibrate_adc_thresholds():
    # pass

def moniter_adc_file(outfile, timeout):
    global LOGFILE
    GPIO.setup(17, GPIO.OUT)           # set GPIO17 as an output
    GPIO.setup(22, GPIO.OUT)           # set GPIO22 as an output
    GPIO.output(22, 0)         # set GPIO22 to 1/GPIO.HIGH/True
    LOGFILE = open(outfile, 'w')
    GPIO.setup(ADC_ALERT_PIN, GPIO.IN)
    GPIO.add_event_detect(ADC_ALERT_PIN, GPIO.BOTH, callback=moniter_adc_isr)  # may want to look into GPIO.RISING || GPIO.FALLING
    ADC.start_adc_comparator(ADC_CHANNEL, 2**16-1, 0, gain=ADC_GAIN, data_rate=ADC_SAMPLE_RATE)
    dac.set_voltage(2048)
    sleep(timeout)
    ADC.stop_adc()
    LOGFILE.close()
    dac.set_voltage(0)


if __name__ == '__main__':
    args = vars(parser.parse_args())
    print(args)
    if args['save'] is not None:
        outfile = open(args['save'], 'w')
        args.pop('save')
    if args['config'] is not None:
        config = json.load(args['config'])
        args.pop('config')
        for entry,val in config.items():
            global entry
            entry = val
    test_adc(**args)
    print(DATA)
    print(len(DATA))
    try:
        outfile.write('timestamp,{}\n'.format(strftime("%Y-%m-%d %H:%M:%S")))
        for entry in DATA:
            outfile.write('{},{}\n'.format(*entry))
        # outfile.write(DATA)
        outfile.close()
    except Exception as e:
        raise(e)
    GPIO.cleanup()
