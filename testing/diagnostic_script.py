#! /usr/bin/env python3

# TODO: get good, then refactor x3

from hal import *
from controller import CONTROL_MAP
from cli_parser import parser, cmds, actions
from version import version as __version__
from utils import load_config,save_config,edit_config

import sys
import json
from collections import deque
from time import strftime, perf_counter, sleep


# globals for routines & ISRs
DATA = deque()
LAST_TIME = 0
CONTROLLER = None
# GLOBAL_VCC = 3.3

hal_init()
# DAC, ADC are already imported

# GPIO ISRs
def diagnostic_adc_isr(channel):
    global DATA, LAST_TIME
    # print('isr_called')
    diagnostic_adc_isr.counter += 1
    ts = perf_counter()
    DATA.append((ADC.get_last_result(), ts-LAST_TIME))
    LAST_TIME = ts
diagnostic_adc_isr.counter = 0

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
        GPIO.output(RELAY_1_PIN, 0)
    elif value < POS_THRESHOLD_LOW:
        print('forward')
        GPIO.output(RELAY_1_PIN, 1)

# routines

# general use routines
def reset_max():
    GPIO.output(RELAY_1_PIN,1)
    ADC.start_adc_comparator(ADC_CHANNEL, 2**16-1, 0, gain=ADC_GAIN, data_rate=ADC_SAMPLE_RATE)
    value = ADC.get_last_result()
    if value >= POS_LIMIT_HIGH:
        print('already at max position')
    else:
        DAC.set_voltage(DEFAULT_DAC_VAL)
        while value <= POS_LIMIT_LOW:
            GPIO.wait_for_edge(ADC_ALERT_PIN, GPIO.BOTH)
            value=ADC.get_last_result()
        DAC.set_voltage(0)
        ADC.stop_adc()
        GPIO.remove_event_detect(ADC_ALERT_PIN)

def reset_min():
    GPIO.output(RELAY_1_PIN,0)
    ADC.start_adc_comparator(ADC_CHANNEL, 2**16-1, 0, gain=ADC_GAIN, data_rate=ADC_SAMPLE_RATE)
    value = ADC.get_last_result()
    if value <= POS_LIMIT_LOW:
        print('already at min position')
    else:
        DAC.set_voltage(DEFAULT_DAC_VAL)
        while value <= POS_LIMIT_LOW:
            GPIO.wait_for_edge(ADC_ALERT_PIN, GPIO.BOTH)
            value=ADC.get_last_result()
        DAC.set_voltage(0)
        ADC.stop_adc()
        GPIO.remove_event_detect(ADC_ALERT_PIN)

def set_position(position):
    flag = False
    value = ADC.get_last_result()
    print(value)
    if value == position:
        return
    if value >= position:
        set_actuator_dir('backward')
    else: #  value < position
        set_actuator_dir('forward')
    DAC_VAL = DEFAULT_DAC_VAL
    DAC.set_voltage(DAC_VAL)
    while True:
        GPIO.wait_for_edge(ADC_ALERT_PIN,GPIO.FALLING)
        value = ADC.get_last_result()
        print(DAC_VAL, value)
        if DAC_VAL == 0:
            print('target achieved')
            print('desired', position)
            print('achieved', value)
            print('error', position-value)
            ADC.stop_adc()
            break
        elif value >= position:  # too far, go back
            # set_actuator_dir('backward')
            GPIO.output(RELAY_1_PIN, 0)
            DAC_VAL >>= 1
            DAC.set_voltage(DAC_VAL)
        else:  # not far enough, go forward
            # set_actuator_dir('forward')
            GPIO.output(RELAY_1_PIN, 1)
            DAC_VAL >>= 1
            DAC.set_voltage(DAC_VAL)

# calibration routines
def calibrate_position():
    """
    calibrate system position thresholds
    """
    global POS_LIMIT_LOW, POS_THRESHOLD_LOW, POS_THRESHOLD_HIGH, POS_LIMIT_HIGH
    print('Beginning calibration routine...')
    # TODO: figure out what relay 2 does
    GPIO.output(RELAY_2_PIN, 0)               # set GPIO22 to 0/GPIO.LOW/False
    GPIO.output(RELAY_1_PIN, 1)               # set default to go forward
    DAC.set_voltage(0)
    print('Setting upper threshold')
    input('Hit enter/return to begin.')
    DAC.set_voltage(1024)
    input('Hit enter/return to mark absolute upper threshold')
    POS_LIMIT_HIGH = ADC.read_adc(ADC_CHANNEL, gain=ADC_GAIN, data_rate=ADC_SAMPLE_RATE)
    DAC.set_voltage(0)
    print(POS_LIMIT_HIGH)
    GPIO.output(RELAY_1_PIN,0)  # prepare to go backwards
    print('Setting lower threshold')
    input('Hit enter/return to begin.')
    DAC.set_voltage(1024)
    input('Hit enter/return to mark absolute lower threshold')
    POS_LIMIT_LOW = ADC.read_adc(ADC_CHANNEL, gain=ADC_GAIN, data_rate=ADC_SAMPLE_RATE)
    DAC.set_voltage(0)
    print(POS_LIMIT_LOW)
    GPIO.output(RELAY_1_PIN,1)  # prepare to go forward
    print('Setting upper desired threshold')
    input('Hit enter/return  to begin.')
    DAC.set_voltage(1024)
    input('Hit enter/return to mark desired upper threshold')
    POS_THRESHOLD_HIGH = ADC.read_adc(ADC_CHANNEL, gain=ADC_GAIN, data_rate=ADC_SAMPLE_RATE)
    DAC.set_voltage(0)
    print(POS_THRESHOLD_HIGH)
    GPIO.output(RELAY_1_PIN,0)  # prepare to go backwards
    print('Setting lower desired threshold')
    input('Hit enter/return  to begin.')
    DAC.set_voltage(1024)
    input('Hit enter/return to mark desired lower threshold')
    POS_THRESHOLD_LOW = ADC.read_adc(ADC_CHANNEL, gain=ADC_GAIN, data_rate=ADC_SAMPLE_RATE)
    DAC.set_voltage(0)
    print(POS_THRESHOLD_LOW)


def set_controller():
    valid_choices = set(map(str,control_map.keys()))
    print('set desired controller')
    print('valid choices:')
    print('1. No adaptave control')
    print('2. P control')
    print('3. PD control')
    choice = input('Enter controller choice: ').strip()
    while choice not in valid_choices:
        choice = input('Enter controller choice: ').strip()
    CONTROLLER = CONTROL_MAP[int(choice)]


def test_configurations():
    global DAC_VAL
    flag = False
    print('Testing current config of:')
    print('Controller: {!s}'.format(CONTROLLER))
    print('Position Thresholds:')
    print('Absolute low: {}'.format(POS_LIMIT_LOW))
    print('Absolute high: {}'.format(POS_LIMIT_HIGH))
    print('Set low: {}'.format(POS_THRESHOLD_LOW))
    print('Set High: {}'.format(POS_THRESHOLD_HIGH))
    GPIO.output(RELAY_1_PIN,1)  # set dir as forward
    DAC_VAL = 1024
    DAC.set_voltage(DAC_VAL)
    ADC.start_adc_comparator(ADC_CHANNEL, 2**16-1, 0, gain=ADC_GAIN, data_rate=ADC_SAMPLE_RATE)
    value = ADC.get_last_result()
    while not flag:
        if value >= POS_LIMIT_HIGH:
            print('Hit absolute max limit', value)
            GPIO.output(RELAY_1_PIN, 0)
            flag = True
        GPIO.wait_for_edge(ADC_ALERT_PIN, GPIO.FALLING)
        value = ADC.get_last_result()
    flag = False
    value = ADC.get_last_result()
    while not flag:
        if value <= POS_LIMIT_LOW:
            print('Hit absolute min limit', value)
            GPIO.output(RELAY_1_PIN, 1)
            flag = True
        GPIO.wait_for_edge(ADC_ALERT_PIN, GPIO.FALLING)
        value = ADC.get_last_result()
    flag = False
    value = ADC.get_last_result()
    while not flag:
        if value >= POS_THRESHOLD_HIGH:
            print('Hit designated max limit', value)
            GPIO.output(RELAY_1_PIN, 0)
            flag = True
            # ADC.stop_adc()
        GPIO.wait_for_edge(ADC_ALERT_PIN, GPIO.FALLING)
        value = ADC.get_last_result()
    flag = False
    value = ADC.get_last_result()
    while not flag:
        if value <= POS_THRESHOLD_LOW:
            DAC.set_voltage(0)
            print('Hit desiginated min limit', value)
            GPIO.output(RELAY_1_PIN, 1)
            flag = True
        GPIO.wait_for_edge(ADC_ALERT_PIN, GPIO.FALLING)
        value = ADC.get_last_result()
    DAC.set_voltage(0)
    ADC.stop_adc()


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
    # set control scheme:
    # set_controller()
    # test:
    test_configurations()
    # reconfigure -- optional
    edit = input('edit configuration? (y/n): ').strip().lower()
    while edit not in ('y','n'):
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
    GPIO.add_event_detect(alert_pin, GPIO.FALLING, callback=diagnostic_adc_isr)  # may want to look into GPIO.RISING || GPIO.FALLING
    # start = perf_counter()
    print('starting loop')
    LAST_TIME=perf_counter()
    ADC.start_adc_comparator(channel,2**16-1,0, gain=gain, data_rate=sample_rate)
    sleep(timeout)
    # while perf_counter() - start < 5:
        # pass
    ADC.stop_adc()


def test_dac(**kwargs):
    raise NotImplementedError('DAC testing not yet implemented')

# acquisition routines
def moniter_adc_file(outfile, timeout, **kwargs):
    global LOGFILE
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


def dispatcher(args):
    if args['cmd'] == 'test_adc':
        test_adc(**args)
    elif args['cmd'] == 'test_dac':
        test_dac(**args)
    elif args['cmd'] == 'test_cal':
        calibrate()
    elif args['cmd'] == 'test_pos':
        # global POS_LIMIT_LOW, POS_THRESHOLD_LOW, POS_THRESHOLD_HIGH, POS_LIMIT_HIGH
        POS_LIMIT_LOW = args['low_min']
        POS_LIMIT_HIGH = args['high_max']
        POS_THRESHOLD_LOW = args['low_threshold']
        POS_THRESHOLD_HIGH = args['high_threshold']
        if args['action'] == 'reset_min':
            reset_min()
        elif args['action'] == 'reset_max':
            reset_max()
        elif args['action'] == 'goto_pos':
            set_position(args['position'])

if __name__ == '__main__':
# GPIO.setup(21,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
    args = vars(parser.parse_args())
    print(args)
    dispatcher(args)
    # ensure stop
    DAC.set_voltage(0)
    ADC.stop_adc()
    GPIO.cleanup()
