#! /usr/bin/env python3

#TODO: get good, then refactor x3

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
    from random import randint
    print('failed to load hardware interfaces, using dummy for general checking')
    def NOP(*args, **kwargs):
        """function that matches any prototype and proceeds to do nothing"""
        pass
    def SOP(*args, **kwargs):
        return randint(0,2**15-1)
    class MCP4725:
        """quick stub class for mcp4725"""
        set_voltage = NOP
    class ADS1115:
        """quick stub class for ADS1115"""
        start_adc = start_adc_comparator = stop_adc  = NOP
        get_last_result = SOP
    class GPIO:
        """quick stub class for GPIO"""
        BCM = IN = RISING = None
        setmode = setup = add_event_detect = cleanup = remove_event_detect = NOP

__version_info = (0,0,2)
__version__ = '.'.join(map(str, __version_info))


# globals for routines & ISRs
DATA = deque()
LAST_TIME = 0
GLOBAL_VCC = 3.3
control_map = {1: None, }
CONTROLLER = None

# pin designations
RELAY_1_PIN = 17
RELAY_2_PIN = 22
ADC_ALERT_PIN = 21

# DAC info
DAC_BITS = 12
DAC_LEVELS = 2**DAC_BITS
DAC_VOLTAGE = GLOBAL_VCC
DAC_STEP_SIZE = DAC_VOLTAGE/DAC_LEVELS
DEFAULT_DAC_VAL = 1024
DAC_VAL = 1024

# ADC info
ADC_GAIN = 1  # configurable, value must be one of: 2/3, 1, 2, 4, 8, 16
ADC_CHANNEL = 1  # configurable, value must be one of: 0, 1, 2, 3
ADC_SAMPLE_RATE = 128  # configurable, value must be: 8, 16, 32, 64, 128, 250, 475, 860
ADC_SAMPLE_BITS = 16
ADC_LEVELS = 2**ADC_SAMPLE_BITS
ADC_PGA_MAP = {2/3 : 6.144,
                                 1 : 4.096,
                                 2 : 2.048,
                                 4 : 1.024,
                                 8 : 0.512,
                                 16 : 0.256,
                                }
ADC_MAX_VOLTAGE = ADC_PGA_MAP[ADC_GAIN]
ADC_STEP_SIZE = 2 * ADC_MAX_VOLTAGE / (2**16)  # volt/step
ADC_MAX_LEVEL = 2**16 / 2 - 1  # hits ADC_MAX_VOLTAGE

# Actuator information
STROKE = 12  # stroke length (INCHES)
POT_VALUE = 10000  # 10k pot
POT_VOLTAGE = 3.3   # connected to a 3V3 supply rail
DISTANCE_PER_VOLT = STROKE / POT_VOLTAGE
ACTUATOR_INCHES_PER_SECOND = {35:{'None':2.00,'Full':1.38},
                                                            50:{'None':1.14,'Full':0.83},
                                                            150:{'None':0.37,'Full':0.28},
                                                            }
DISTANCE_PER_LEVEL = ADC_STEP_SIZE * DISTANCE_PER_VOLT  # inches / step

# default Thresholds
POS_LIMIT_LOW = 10
POS_THRESHOLD_LOW = 750
POS_THRESHOLD_HIGH = 17800
POS_LIMIT_HIGH = round(GLOBAL_VCC / ADC_MAX_VOLTAGE * ADC_MAX_LEVEL)

# TODO: implement subparsers
# input options parser
parser = ArgumentParser() # 'elastocaloric testing'
# parser.add_argument('-c', '--channel', type=int, choices=(1,2,3,4), help='ADC input channel', default=ADC_CHANNEL)
parser.add_argument('-r', '--sample_rate', type=int, choices=(8, 16, 32, 64, 128, 250, 475, 860),
                                    default=ADC_SAMPLE_RATE, help='Sample rate for ADC')
# parser.add_argument('-a','--alert_pin', type=int, default=ADC_ALERT_PIN, help='RPI gpio pin number (eg: gpio27 -> "-a 27")')
# parser.add_argument('-p','--polarity', type=int, choices=(-1,+1), default=ADC_POLARITY, help='ADC input polarity (1, -1)')
parser.add_argument('-g','--gain', type=float, choices=(2/3,1,2,3,8,16), default=ADC_GAIN, help='ADC input polarity (1, -1)')
parser.add_argument('-t','--timeout', type=int, default=5, help='set timout for loop')
parser.add_argument('-o','--outfile', type=str, default=None, help='optional file to save results to')
parser.add_argument('--config', type=str, default=None, help='optional configuration file')
parser.add_argument('-V', '--version', action='version', version='%(prog)s {}'.format(__version__))


# human readable conversion functions
def level2voltage(level):
    return level * ADC_STEP_SIZE

def level2position(level):
    return level * DISTANCE_PER_LEVEL

def mm2in(mmlength):
    return mmlength * 0.0393701

def in2mm(inlength):
    return inlength * 25.4

def lbs2kg(lbs):
    return lbs * 0.453592

def kg2lbs(kg):
    return kg * 2.20462

# HW abstractions
DAC = MCP4725()
ADC = ADS1115()
GPIO.setmode(GPIO.BCM)    # choose BCM or BOARD

# GPIO ISRs
def reset_min_pos_isr(channel):
    """
    Resets actuator back to min threshold. Sets direction relay to go forward.

    To use:
    1. register ISR callback
    2. start motor backward
    3. start ADC monitoring
    """
    value = ADC.get_last_result()
    # print(value)
    if value <= POS_LIMIT_LOW:  # Hit limit -- Done, derigester and stop
        GPIO.output(RELAY_1_PIN, 1)
        DAC.set_voltage(0)
        GPIO.remove_event_detect(channel)
        ADC.stop_adc()

def reset_max_pos_isr(channel):
    """
    Resets actuator back to max threshold. Sets direction relay to go backward.

    To use:
    1. register ISR callback
    2. start the motor forward
    3. start ADC monitoring
    """
    value = ADC.get_last_result()
    # print(value)
    if value >= POS_LIMIT_HIGH:  # Hit limit -- Done, derigester and stop
        GPIO.output(RELAY_1_PIN, 0)
        DAC.set_voltage(0)
        GPIO.remove_event_detect(channel)
        ADC.stop_adc()

def set_desired_pos(channel, pos):
    """
    Sets actuator to desired threshold.
    should be called via a lambda function
    eg:
    GPIO.add_event_detect(channel, GPIO.RISING, callback=lambda ch:set_desired_pos(ch,<DESIRED_POSITION>))

    To use:
    1. register ISR callback
    2. start the motor in a direction at some speed, speed will be decreased to make positing as accurate as possible
    3. start ADC monitoring
    """
    value = ADC.get_last_result()
    # print(value)
    if DAC_VAL == 0:
        print('target achieved')
        print('desired', pos)
        print('achieved', value)
        print('error', abs(pos-value))
        DAC.set_voltage(0)
        GPIO.remove_event_detect(channel)
        ADC.stop_adc()
    elif value >= pos:  # too far, go back
        GPIO.output(RELAY_1_PIN, 0)
        if  set_desired_pos.flag:  # slow down
            DAC_VAL //=2
            DAC.set_voltage(DAC_VAL)
        else:
            DAC_VAL = DEFAULT_DAC_VAL
            DAC.set_voltage(DAC_VAL)
    else:  # not far enough, go forward
        GPIO.output(RELAY_1_PIN,1)
        if set_desired_pos.flag:
            DAC_VAL //=2
            DAC.set_voltage(DAC_VAL)
        else:
            DAC_VAL = DEFAULT_DAC_VAL
set_desired_pos.flag = False  # flag var to initiate homing in on target position

def diagnostic_adc_isr(channel):
    global DATA, LAST_TIME
    ts = perf_counter()
    DATA.append((ADC.get_last_result(), ts-LAST_TIME))
    LAST_TIME = ts

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
    if value >= POS_THRESHOLD_HIGH:
        print('reverse')
        GPIO.output(17, 0)
    elif value < POS_THRESHOLD_LOW:
        print('forward')
        GPIO.output(17, 1)

def position_test_isr(channel):
    value = ADC.get_last_result()
    if value >= POS_LIMIT_HIGH:
        print('Hit absolute max limit')
        GPIO.output(17, 0)
        position_test_isr.flag = True
    elif value >= POS_THRESHOLD_HIGH and position_test_isr.flag:
        print('Hit designated max limit')
        GPIO.output(17, 0)
        DAC.set_voltage(0)
        position_test_isr.flag = False
        # ADC.stop_adc()
    elif value <= POS_THRESHOLD_LOW and position_test_isr.flag:
        print('Hit desiginated min limit')
        GPIO.output(17, 1)
        DAC.set_voltage(0)
        position_test_isr.flag = False
        # ADC.stop_adc()
    elif value <= POS_LIMIT_LOW:
        print('Hit absolute min limit')
        GPIO.output(17, 1)
        position_test_isr.flag = True
position_test_isr.flag = False

# routines

# calibration routines
def calibrate_position():
    """
    calibrate system position thresholds
    """
    # global POS_LIMIT_LOW, POS_THRESHOLD_LOW, POS_THRESHOLD_HIGH, POS_LIMIT_HIGH
    print('Beginning calibration routine...')
    GPIO.setup(ADC_ALERT_PIN, GPIO.IN)
    GPIO.setup(RELAY_1_PIN, GPIO.OUT)   # set GPIO17 as an output
    GPIO.setup(RELAY_2_PIN, GPIO.OUT)   # set GPIO22 as an output

    # TODO: figure out what relay 2 does
    GPIO.output(RELAY_2_PIN, 0)               # set GPIO22 to 0/GPIO.LOW/False

    DAC.set_voltage(0)
    GPIO.output(RELAY_1_PIN, 1)               # set default to go forward
    print('Setting upper threshold')
    input('Hit any key to begin.')
    DAC.set_voltage(1024)
    input('Hit any key to mark absolute upper threshold')
    POS_LIMIT_HIGH = ADC.read_adc(ADC_CHANNEL, gain=ADC_GAIN, data_rate=ADC_SAMPLE_RATE)
    DAC.set_voltage(0)

    DAC.set_voltage(0)
    GPIO.output(RELAY_1_PIN,0)  # prepare to go backwards
    print('Setting lower threshold')
    input('Hit any key to begin.')
    DAC.set_voltage(1024)
    input('Hit any key to mark absolute lower threshold')
    POS_LIMIT_LOW = ADC.read_adc(ADC_CHANNEL, gain=ADC_GAIN, data_rate=ADC_SAMPLE_RATE)
    DAC.set_voltage(0)

    DAC.set_voltage(0)
    GPIO.output(RELAY_1_PIN,1)  # prepare to go forward
    print('Setting upper desired threshold')
    input('Hit any key to begin.')
    DAC.set_voltage(1024)
    input('Hit any key to mark desired upper threshold')
    POS_THRESHOLD_HIGH = ADC.read_adc(ADC_CHANNEL, gain=ADC_GAIN, data_rate=ADC_SAMPLE_RATE)
    DAC.set_voltage(0)

    DAC.set_voltage(0)
    GPIO.output(RELAY_1_PIN,0)  # prepare to go backwards
    print('Setting lower desired threshold')
    input('Hit any key to begin.')
    DAC.set_voltage(1024)
    input('Hit any key to mark desired lower threshold')
    POS_THRESHOLD_LOW = ADC.read_adc(ADC_CHANNEL, gain=ADC_GAIN, data_rate=ADC_SAMPLE_RATE)
    DAC.set_voltage(0)

def set_controller():
    valid_choices = {'1'}
    print('set desired controller')
    print('valid choices:')
    print('1. No adaptave control')
    # print('2. P control')
    # print('3. PD control')
    choice = input('Enter controller choice: ').strip()
    while choice not in valid_choices:
        choice = input('Enter controller choice: ').strip()
    CONTROLLER = control_map[int(choice)]

def test_configurations():
    print('Testing current config of:')
    print('Controller: {!s}'.format(CONTROLLER))
    print('Position Thresholds:')
    print('Absolute low: {}'.format(POS_LIMIT_LOW))
    print('Absolute high: {}'.format(POS_LIMIT_HIGH))
    print('Set low: {}'.format(POS_THRESHOLD_LOW))
    print('Set High: {}'.format(POS_THRESHOLD_HIGH))
    GPIO.SET(RELAY_1_PIN,1)  # set dir as forward
    DAC_VAL = 1024
    DAC.set_voltage(DAC_VAL)
    ADC.start_adc_comparator(ADC_CHANNEL, 2**16-1, 0, gain=ADC_GAIN, data_rate=ADC_SAMPLE_RATE)


def load_config(cfg_path):
    pass

def save_cfg(cfg_path):
    pass

def edit_config(cfg_path):
    pass


def calibrate():
    """
    calibrate actuator control
    allows for :
        thresholding:
            software implemented stroke boundaries
            safety and desired operating stroke definitions
        control method:
            P control - output speed is proportional to desired position to approach that position
            PD control - P control + output speed is modified by the rate of approach
            None - output speed is flat over entire duration
        testing and editing of generated parameters:
            test currently generated scheme
            editing any single point generated

    7 step process:
        1. define abs low (leave alone if limit switch)
        2. define abs high (leave alone if limit switch)
        3. define desired stroke low threshold
        4. define desired stroke high threshold
        5. define control (P,PD, None)
        6. define desired actuator movement rates
        6.5. test current setup -- tweak values as wanted
        7. confirm cal data
    """
    # calibrate thresholds:
    calibrate_position()
    # NOT IMPLEMENTED YET
    # set control scheme:
    # set_controller()
    # test:
    test_configurations()
    # reconfigure -- optional
    edit = input('edit configuration? (y/n): ').strip().lower()
    while editnot in ('y','n'):
        edit = input('edit configuration? (y/n): ').strip().lower()
    if edit == 'y':
        edit_config()

    # confirm
    confirm = input ('confirm settings? (y/n): ').strip().lower()
    while confirm.lower() not in ('y','n'):
        confirm = input ('confirm settings? (y/n): ').strip().lower()
    if confirm == 'y':
        save_config()

# diagnostic_routines
def test_adc(alert_pin=ADC_ALERT_PIN, channel=ADC_CHANNEL, sample_rate=ADC_SAMPLE_RATE, gain=ADC_GAIN,  timeout=5, **kwargs):
    max_voltage = ADC_PGA_MAP[gain]
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

# acquisition routines
def moniter_adc_file(outfile, timeout, **kwargs):
    global LOGFILE
    GPIO.setup(17, GPIO.OUT)           # set GPIO17 as an output
    GPIO.setup(22, GPIO.OUT)           # set GPIO22 as an output
    GPIO.output(22, 0)         # set GPIO22 to 1/GPIO.HIGH/True
    LOGFILE = open(outfile, 'w')
    GPIO.setup(ADC_ALERT_PIN, GPIO.IN)
    GPIO.add_event_detect(ADC_ALERT_PIN, GPIO.BOTH, callback=moniter_adc_isr)  # may want to look into GPIO.RISING || GPIO.FALLING
    ADC.start_adc_comparator(ADC_CHANNEL, 2**16-1, 0, gain=ADC_GAIN, data_rate=ADC_SAMPLE_RATE)
    DAC.set_voltage(2048)
    sleep(timeout)
    ADC.stop_adc()
    LOGFILE.close()
    DAC.set_voltage(0)

# until funcs
def cleanup_log(logfile):
    """
    base cleanup function that provides basic file cleanup for formatting things like timesteps
    """
    raise NotImplementedError()


if __name__ == '__main__':
    args = vars(parser.parse_args())
    print(args)
    if args['outfile'] is not None:
        moniter_adc_file(**args)
    if args['config'] is not None:
        config = json.load(args['config'])
        args.pop('config')
        # for entry,val in config.items():
            # global entry
            # entry = val
    # test_adc(**args)
    # print(DATA)
    # print(len(DATA))
    # try:
        # outfile.write('timestamp,{}\n'.format(strftime("%Y-%m-%d %H:%M:%S")))
        # for entry in DATA:
            # outfile.write('{},{}\n'.format(*entry))
        # # outfile.write(DATA)
        # outfile.close()
    # except Exception as e:
        # raise(e)
    DAC.set_voltage(0)
    GPIO.cleanup()
