#! /urs/bin/env python3
"""
motor control script

Must have:
    high precision
    0.1 mm (3.93701 thou) accuracy
"""

import sys
from collections import deque
from argparse import ArgumentParser
from time import sleep, strftime, time, perf_counter

# import hardware interfaces
from Adafruit_ADS1x15 import ADS1115
from Adafruit_MCP4725 import MCP4725
import RPi.GPIO as GPIO

# Actuator information
# used to help map voltage to distance
STROKE = 12  # stroke length (INCHES)
POT_VALUE = 10000  # 10k pot
POT_VOLTAGE = 3.3  # connected to a 3V3 supply rail
DISTANCE_PER_VOLT = STROKE / POT_VOLTAGE
# (pos*POT_VALUE / ((1-pos)*POT_VALUE))

ACTUATOR_INCHES_PER_SECOND = {35:{'None':2.00,
                                                                    'Full':1.38},
                                                            50:{'None':1.14,
                                                                   'Full':0.83},
                                                            150:{'None':0.37,
                                                                     'Full':0.28},
                                                            }

# ADC setup
ADC_CHANNEL = 1

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
ADC_MAX_VOLTAGE = ADC_POLARITY * ADC_MAP[ADC_GAIN]
ADC_STEP_SIZE = abs(ADC_MAX_VOLTAGE / 2**16)  # volt/step

#ADS1115 data rate settings:
# Valid values are: 8, 16, 32, 64, 128, 250, 475, 860 -- default is 128sps
ADC_SAMPLE_RATE = 860  # note that bit-rate throughput will be > 16*ADC_SAMPLE_RATE due to i2c overhead

# instantiate hardware instances
adc = Adafruit_ADS1x15.ADS1115()
dac = Adafruit_MCP4725.MCP4725()

# config interfaces
GPIO.setmode(GPIO.BCM)    # choose BCM or BOARD
GPIO.setup(17, GPIO.OUT)   # set GPIO17 as an output  # relay one
GPIO.setup(22, GPIO.OUT)   # set GPIO22 as an output  # relay two

# start hardware:
GPIO.output(22, 0)               # set GPIO22 to Low
adc.start_adc(ADC_CHANNEL, gain=ADC_GAIN, data_rate=ADC_SAMPLE_RATE)


#dac.set_voltage(0)
#dac.set_voltage(644)
#dac.set_voltage(656)
#dac.set_voltage(672)
#dac.set_voltage(688)
#dac.set_voltage(704)
#dac.set_voltage(720)
#dac.set_voltage(752)
#dac.set_voltage(768)
dac.set_voltage(1024)
#dac.set_voltage(2048)
#dac.set_voltage(3072)
#dac.set_voltage(4096)

# time.sleep(0.2)

def moniter_adc_file(timeout, outfile):
    """
    Implements a timed monitoring of the adc values.
    Saves readings to outfile
    :param timeout: timeout in seconds
    :param outfile: filename to save files to
    """
    with open(outfile,'a') as log:
        print('Reading ADS1x15 channel 0 for 1800 seconds...')
        log.write('timestamp,{}\n'.format(strftime("%Y-%m-%d %H:%M:%S")))
        start = perf_counter()
        while time() - start < timeout:
            value = adc.get_last_result()
            log.write("{},{}\n".format(perf_counter()-start,value))
                if (value <= 750):
                    GPIO.output(17, 1)
                    # sleep(0.05)
                elif (value >= 17800):
                    GPIO.output(17, 0)
                    # sleep(0.05)
                # else:
                    # sleep(0.05)
        print('Go to the start position')

        while (value > 750): # Read the last ADC conversion value and print it out.
            value = adc.get_last_result()
            print('Channel 1: {0}'.format(value))
            GPIO.output(17, 0)
            # sleep(0.05)

        # stop peripherals, cleanup
        adc.stop_adc()
        dac.set_voltage(0)
        GPIO.cleanup()


def moniter_adc_ram(timeout):
    """
    Implements a timed monitoring of the adc values.
    keeps reading in ram, avoids file io overhead
    """
    data_buf = deque()
    print('Reading ADS1x15 channel 0 for 1800 seconds...')
    data_buf.append(('timestamp',strftime("%Y-%m-%d %H:%M:%S"),))
    start = perf_counter()
    while time() - start < timeout:
        value = adc.get_last_result()
        data_buf.append((perf_counter()-start,value))
            if (value <= 750):
                GPIO.output(17, 1)
                # sleep(0.05)
            elif (value >= 17800):
                GPIO.output(17, 0)
                # sleep(0.05)
            # else:
                # sleep(0.05)
    print('Go to the start position')

    while (value > 750): # Read the last ADC conversion value and print it out.
        value = adc.get_last_result()
        print('Channel 1: {0}'.format(value))
        GPIO.output(17, 0)
        # sleep(0.05)

    # stop peripherals, cleanup
    adc.stop_adc()
    dac.set_voltage(0)
    GPIO.cleanup()

def set_config(config_file):
    pass

parser = ArgumentParser()
parser.add_argument('outfile', type=str, help='Output file storage name')
parser.add_argument('media', nargs='?', choices=('file', 'ram'), default='file',
                                    help='whether to build data set in memory or directly in file')
parser.add_argument('--config_file', type=str, help='config file to pull settings from (json)')

if __name__ == '__main__':
    args = parser.parse_args()
    if args.config_file is not None:
        set_config(args.config)
    if args.media == 'ram':
        res = moniter_adc_ram(args.outfile)
        with open(args.outfilefile, 'w') as f:
            for entry in res:
                f.write(entry + '\n')
    elif args.media == 'file':
        moniter_adc_file(args.outfile)
    else:
        print('Unknown save option: "{}"'.format(args.outfile))