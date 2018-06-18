#! /usr/bin/env python3

# TODO: check if refactor works

import os
from collections import deque
from time import (
    strftime,
    perf_counter,
    # sleep,
)

# noinspection PyUnresolvedReferences
from version import version as __version__
from libs.utils import cfg_formatter
from libs.controller import CONTROL_MAP
from launch.cli_parser import (
    parser,
    cmds,
    actions,
)
from hal import (
    ADC,
    DAC,
    PINS,
    UNITS,
    GPIO,
    Actuator,
    hal_init,
    hal_cleanup,
)

# globals for routines & ISRs
####################################################
DATA = deque()
LAST_TIME = 0
CONTROLLER = None
LOGFILE = None
WAIT_TIMEOUT = 2  # 2ms max wait -- 0.1016mm tolerance theoretical
TIMEOUT = 5
OUTFILE = None
# GLOBAL_VCC = 3.3

hal_init()  # setup hw


# GPIO ISRs
####################################################
# noinspection PyUnusedLocal
def diagnostic_adc_isr(channel):
    global LAST_TIME
    # print('isr_called')
    ts = perf_counter()
    DATA.append((ADC.get_last_result(), ts - LAST_TIME))
    LAST_TIME = ts


# noinspection PyUnusedLocal
def monitor_adc_isr(channel):
    global LOGFILE, LAST_TIME
    ts = perf_counter()
    value = ADC.get_last_result()
    LOGFILE.write('{},{}\n'.format(value, ts - LAST_TIME))
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
    if value >= Actuator.pos_threshold_high:
        Actuator.set_actuator_dir('backward')
        print('reverse')
        # GPIO.output(PINS['relay_1'], 0)

    elif value < Actuator.pos_threshold_low:
        Actuator.set_actuator_dir('forward')
        print('forward')
        # GPIO.output(PINS['relay_1'], 1)


# routines
####################################################
# general use routines
def reset_max():
    GPIO.output(PINS['relay_1'], 1)
    ADC.start_conversions()
    # ADC.start_adc_comparator(ADC.default_channel, 2 ** 16 - 1, 0, gain=ADC.gain, data_rate=ADC.sample_rate)
    value = ADC.get_last_result()
    if value >= Actuator.pos_limit_high:
        print('already at max position')
    else:
        DAC.set_voltage(DAC.default_val)
        while value <= Actuator.pos_limit_low:
            GPIO.wait_for_edge(PINS['adc_alert'], GPIO.BOTH, timeout=WAIT_TIMEOUT)
            value = ADC.get_last_result()
        DAC.set_voltage(DAC.stop)
        ADC.stop_adc()
        GPIO.remove_event_detect(PINS['adc_alert'])


def reset_min():
    GPIO.output(PINS['relay_1'], 0)
    ADC.start_adc_comparator(ADC.default_channel, 2 ** 16 - 1, 0, gain=ADC.gain, data_rate=ADC.sample_rate)
    value = ADC.get_last_result()
    if value <= Actuator.pos_limit_low:
        print('already at min position')
    else:
        DAC.set_voltage(DAC.default_val)
        while value <= Actuator.pos_limit_low:
            GPIO.wait_for_edge(PINS['adc_alert'], GPIO.BOTH, timeout=WAIT_TIMEOUT)
            value = ADC.get_last_result()
        DAC.set_voltage(DAC.stop)
        ADC.stop_adc()
        GPIO.remove_event_detect(PINS['adc_alert'])


def set_position(position):
    value = ADC.get_last_result()
    print(value)
    if value == position:
        return
    if value >= position:
        Actuator.set_actuator_dir('backward')
    else:  # value < position
        Actuator.set_actuator_dir('forward')
    DAC.value = DAC.default_val
    DAC.set_voltage(DAC.value)
    while True:
        GPIO.wait_for_edge(PINS['adc_alert'], GPIO.FALLING, timeout=WAIT_TIMEOUT)
        value = ADC.get_last_result()
        print(DAC.value, value)
        if DAC.value == 0:
            print('target achieved')
            print('desired', position)
            print('achieved', value)
            print('error', position - value)
            ADC.stop_adc()
            break
        elif value >= position:  # too far, go back
            # Actuator.set_actuator_dir('backward')
            GPIO.output(PINS['relay_1'], 0)
            DAC.value >>= 1
            DAC.set_voltage(DAC.value)
        else:  # not far enough, go forward
            # Actuator.set_actuator_dir('forward')
            GPIO.output(PINS['relay_1'], 1)
            DAC.value >>= 1
            DAC.set_voltage(DAC.value)


# calibration routines
def calibrate_position():
    """
    hand calibrate system position thresholds
    """
    print('Beginning calibration routine...')
    # TODO: figure out what relay 2 does
    GPIO.output(PINS['relay_2'], 0)  # set GPIO22 to 0/GPIO.LOW/False
    GPIO.output(PINS['relay_1'], 1)  # set default to go forward
    DAC.set_voltage(DAC.stop)
    print('Setting upper threshold')
    input('Hit enter/return to begin.')
    DAC.set_voltage(DAC.default_val)
    input('Hit enter/return to mark absolute upper threshold')
    Actuator.pos_limit_high = ADC.read_adc(ADC.default_channel, gain=ADC.gain, data_rate=ADC.sample_rate)
    DAC.set_voltage(DAC.stop)
    print(Actuator.pos_limit_high)
    GPIO.output(PINS['relay_1'], 0)  # prepare to go backwards
    print('Setting lower threshold')
    input('Hit enter/return to begin.')
    DAC.set_voltage(DAC.default_val)
    input('Hit enter/return to mark absolute lower threshold')
    Actuator.pos_limit_low = ADC.read_adc(ADC.default_channel, gain=ADC.gain, data_rate=ADC.sample_rate)
    DAC.set_voltage(DAC.stop)
    print(Actuator.pos_limit_low)
    GPIO.output(PINS['relay_1'], 1)  # prepare to go forward
    print('Setting upper desired threshold')
    input('Hit enter/return  to begin.')
    DAC.set_voltage(DAC.default_val)
    input('Hit enter/return to mark desired upper threshold')
    Actuator.pos_threshold_high = ADC.read_adc(ADC.default_channel, gain=ADC.gain, data_rate=ADC.sample_rate)
    DAC.set_voltage(DAC.stop)
    print(Actuator.pos_threshold_high)
    GPIO.output(PINS['relay_1'], 0)  # prepare to go backwards
    print('Setting lower desired threshold')
    input('Hit enter/return  to begin.')
    DAC.set_voltage(DAC.default_val)
    input('Hit enter/return to mark desired lower threshold')
    Actuator.pos_threshold_low = ADC.read_adc(ADC.default_channel, gain=ADC.gain, data_rate=ADC.sample_rate)
    DAC.set_voltage(DAC.stop)
    print(Actuator.pos_threshold_low)


def set_controller():
    global CONTROLLER
    valid_choices = set(map(str, CONTROL_MAP.keys()))
    print('set desired controller')
    print('valid choices:')
    print('1. No adaptive control')
    print('2. P control')
    print('3. PD control')
    print('4. PI control')
    print('5. PID control')
    choice = input('Enter controller choice: ').strip()
    while choice not in valid_choices:
        choice = input('Enter controller choice: ').strip()
    CONTROLLER = CONTROL_MAP[int(choice)]


def test_configurations():
    flag = False
    print('Testing current config of:')
    print('Controller: {!s}'.format(CONTROLLER))
    print('Position Thresholds:')
    print('Absolute low: {}'.format(Actuator.pos_limit_low))
    print('Absolute high: {}'.format(Actuator.pos_limit_high))
    print('Set low: {}'.format(Actuator.pos_threshold_low))
    print('Set High: {}'.format(Actuator.pos_threshold_high))
    Actuator.set_actuator_dir('forward')
    # GPIO.output(PINS['relay_1'], 1)  # set dir as forward
    DAC.value = 1024
    DAC.set_voltage(DAC.value)
    value = ADC.start_adc_comparator(ADC.default_channel, 2 ** 16 - 1, 0, gain=ADC.gain, data_rate=ADC.sample_rate)
    while not flag:
        if value >= Actuator.pos_limit_high:
            print('Hit absolute max limit', value)
            Actuator.set_actuator_dir('backward')
            # GPIO.output(PINS['relay_1'], 0)
            flag = True
        # GPIO.wait_for_edge(PINS['adc_alert'], GPIO.FALLING, timeout=WAIT_TIMEOUT)
        ADC.wait_for_sample(timeout=WAIT_TIMEOUT)
        value = ADC.get_last_result()
    flag = False
    value = ADC.get_last_result()
    while not flag:
        if value <= Actuator.pos_limit_low:
            print('Hit absolute min limit', value)
            Actuator.set_actuator_dir('forward')
            # GPIO.output(PINS['relay_1'], 1)
            flag = True
        # GPIO.wait_for_edge(PINS['adc_alert'], GPIO.FALLING, timeout=WAIT_TIMEOUT)
        ADC.wait_for_sample(timeout=WAIT_TIMEOUT)
        value = ADC.get_last_result()
    flag = False
    value = ADC.get_last_result()
    while not flag:
        if value >= Actuator.pos_threshold_high:
            print('Hit designated max limit', value)
            Actuator.set_actuator_dir('backward')
            # GPIO.output(PINS['relay_1'], 0)
            flag = True
            # ADC.stop_adc()
        # GPIO.wait_for_edge(PINS['adc_alert'], GPIO.FALLING, timeout=WAIT_TIMEOUT)
        ADC.wait_for_sample(timeout=WAIT_TIMEOUT)
        value = ADC.get_last_result()
    flag = False
    value = ADC.get_last_result()
    while not flag:
        if value <= Actuator.pos_threshold_low:
            DAC.set_voltage(DAC.stop)
            print('Hit designated min limit', value)
            Actuator.set_actuator_dir('forward')
            # GPIO.output(PINS['relay_1'], 1)
            flag = True
        # GPIO.wait_for_edge(PINS['adc_alert'], GPIO.FALLING, timeout=WAIT_TIMEOUT)
        ADC.wait_for_sample(timeout=WAIT_TIMEOUT)
        value = ADC.get_last_result()
    DAC.set_voltage(DAC.stop)
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
    # edit = input('edit configuration? (y/n): ').strip().lower()
    # while edit not in ('y','n'):
    #     edit = input('edit configuration? (y/n): ').strip().lower()
    # if edit == 'y':
    #     edit_config()
    # confirm
    confirm = input('confirm settings? (y/n): ').strip().lower()
    while confirm not in ('y', 'n'):
        confirm = input('confirm settings? (y/n): ').strip().lower()
    if confirm == 'y':
        outfile = input('enter valid config file name: ').strip()
        while not os.access(os.path.dirname(outfile), os.W_OK):
            outfile = input('enter valid config file name: ').strip()
        save_config(outfile)


# diagnostic_routines
# noinspection PyUnusedLocal
def test_adc(alert_pin=ADC.alert_pin, channel=ADC.default_channel, sample_rate=ADC.sample_rate,
             gain=ADC.gain, timeout=5, **kwargs):
    abs_start = perf_counter()
    GPIO.setup(alert_pin, GPIO.IN)
    GPIO.add_event_detect(alert_pin, GPIO.FALLING, callback=diagnostic_adc_isr)
    # start = perf_counter()
    print('starting loop')
    ADC.start_adc_comparator(channel, 2 ** 16 - 1, 0, gain=gain, data_rate=sample_rate)
    start_time = perf_counter()
    global LAST_TIME
    # sleep(timeout)
    while perf_counter() - start_time < timeout:
        ADC.wait_for_sample(timeout=WAIT_TIMEOUT)
        # print('isr_called')
        ts = perf_counter()
        DATA.append((ADC.get_last_result(), ts - LAST_TIME))
        LAST_TIME = ts
    ADC.stop_adc()
    print('executed in {:6f}s:'.format(perf_counter() - abs_start))
    print('{} samples captured in {} seconds. Average of {}sps'.format(len(DATA), timeout, len(DATA) / timeout))
    return DATA


# noinspection PyUnusedLocal
def test_dac(**kwargs):
    raise NotImplementedError('DAC testing not yet implemented')


# acquisition routines
# noinspection PyUnusedLocal
def monitor_adc_file(outfile, timeout, **kwargs):
    global LOGFILE
    GPIO.output(PINS['relay_2'], GPIO.LOW)  # set GPIO22 to 1/GPIO.HIGH/True
    LOGFILE = open(outfile, 'w')
    LOGFILE.write('timestamp,{}\n'.format(strftime("%Y-%m-%d %H:%M:%S")))
    GPIO.setup(ADC.alert_pin, GPIO.IN)
    GPIO.add_event_detect(ADC.alert_pin, GPIO.FALLING, callback=monitor_adc_isr)
    ADC.start_conversions()
    # ADC.start_adc_comparator(ADC.default_channel, 2 ** 16 - 1, 0, gain=ADC.gain, data_rate=ADC.sample_rate)
    DAC.set_voltage(DAC.default_val)
    start_time = perf_counter()
    while perf_counter() - start_time < timeout:
        ADC.wait_for_sample(timeout=WAIT_TIMEOUT)
        monitor_adc_isr(ADC.alert_pin)
    # sleep(timeout)
    ADC.stop_adc()
    LOGFILE.close()
    DAC.set_voltage(DAC.stop)


# util funcs
# config handling
def load_config(cfg_path):
    with open(cfg_path, 'r') as cfg_file:
        config = cfg_formatter.load(cfg_file)
    # for key, val in config.items():
    #     globals()[key] = val
    return config
    # from pprint import pprint
    # pprint(globals())


def save_config(cfg_path):
    with open(cfg_path, 'w') as cfg_file:
        cfg_formatter.dump({'POS_LIMIT_LOW': Actuator.pos_limit_low,
                            'POS_LIMIT_HIGH': Actuator.pos_limit_high,
                            'POS_THRESHOLD_LOW': Actuator.pos_threshold_low,
                            'POS_THRESHOLD_HIGH': Actuator.pos_threshold_high,
                            'SAMPLE_RATE': ADC.sample_rate,
                            'TIMEOUT': TIMEOUT,
                            'UNITS': UNITS,
                            'OUTFILE': OUTFILE,
                            },
                           cfg_file
                           )


def edit_config(cfg_path):
    pass


def dispatcher(arg_dict):
    if arg_dict['config'] is not None:
        global TIMEOUT, OUTFILE
        cfg = load_config(arg_dict['config'])
        # coalesce = lambda key: cfg[key] or arg_dict[key]
        arg_dict.update({'timeout': cfg['TIMEOUT'] or arg_dict['timeout'],
                         'sample_rate': cfg['ADC.sample_rate'] or arg_dict['sample_rate'],
                         'outfile': cfg['OUTFILE'] or arg_dict['outfile'],
                         'units': cfg['UNITS'] or arg_dict['units'],
                         'high_max': cfg['POS_LIMIT_HIGH'] or arg_dict['high_max'],
                         'low_min': cfg['POS_LIMIT_LOW'] or arg_dict['low_min'],
                         'high_threshold': cfg['POS_THRESHOLD_HIGH'] or arg_dict['high_threshold'],
                         'low_threshold': cfg['POS_THRESHOLD_LOW'] or arg_dict['low_threshold'],
                         })
        ADC.sample_rate = arg_dict['sample_rate']
        TIMEOUT = arg_dict['timeout']
        OUTFILE = arg_dict['outfile']
    print(arg_dict)
    if arg_dict['cmd'] == cmds['TEST_ADC']:
        test_adc()
    elif arg_dict['cmd'] == cmds['TEST_DAC']:
        test_dac(**arg_dict)
    elif arg_dict['cmd'] == cmds['TEST_CAL']:
        calibrate()
    elif arg_dict['cmd'] == cmds['TEST_POS']:
        Actuator.pos_limit_low = arg_dict.pop('low_min')
        Actuator.pos_limit_high = arg_dict.pop('high_max')
        Actuator.pos_threshold_low = arg_dict.pop('low_threshold')
        Actuator.pos_threshold_high = arg_dict['high_threshold']
        if arg_dict['action'] == actions['RESET_MIN']:
            reset_min()
        elif arg_dict['action'] == actions['RESET_MAX']:
            reset_max()
        elif arg_dict['action'] == actions['GOTO_POS']:
            set_position(arg_dict['position'])
    elif arg_dict['cmd'] == cmds['RUN_ACQ']:
        monitor_adc_file(**arg_dict)
    else:
        print('command "{}" not known'.format(arg_dict['cmd']))


if __name__ == '__main__':
    args = vars(parser.parse_args())
    # print(args)
    dispatcher(args)
    # ensure stop
    hal_cleanup()
