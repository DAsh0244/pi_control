#! /usr/bin/env python3
import os
from collections import deque
from time import (
    strftime,
    perf_counter,
    # sleep,
)
# noinspection PyUnresolvedReferences
from libs.utils import cfg_formatter, get_k_value
from libs.controller import (
    PController,
    PDController,
    PIController,
    PIDController
)
from launch.cli_parser import (
    parser,
    cmds,
)
from libs.hal import (
    adc,
    dac,
    PINS,
    UNITS,
    GPIO,
    actuator,
    hal_init,
    hal_cleanup,

)

from orchestration import action_map
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
    DATA.append((adc.get_last_result(), ts - LAST_TIME))
    LAST_TIME = ts


# noinspection PyUnusedLocal
def monitor_adc_isr(channel):
    global LOGFILE, LAST_TIME
    ts = perf_counter()
    value = adc.get_last_result()
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
    if value >= actuator.pos_threshold_high:
        actuator.set_actuator_dir('backward')
        print('reverse')
        # GPIO.output(PINS['relay_1'], 0)

    elif value < actuator.pos_threshold_low:
        actuator.set_actuator_dir('forward')
        print('forward')
        # GPIO.output(PINS['relay_1'], 1)


# routines
####################################################
# general use routines
def reset_max():
    actuator.set_position(actuator.pos_limit_high)


def reset_min():
    actuator.set_position(actuator.pos_limit_low)


# calibration routines
def calibrate_position():
    """
    hand calibrate system position thresholds
    """
    print('Beginning calibration routine...')
    actuator.set_actuator_dir('forward')
    dac.set_voltage(dac.stop)
    print('Setting upper threshold')
    input('Hit enter/return to begin.')
    dac.set_voltage(dac.default_val)
    input('Hit enter/return to mark absolute upper threshold')
    actuator.pos_limit_high = adc.read_adc(adc.default_channel, gain=adc.gain, data_rate=adc.sample_rate)
    dac.set_voltage(dac.stop)
    print(actuator.pos_limit_high)
    GPIO.output(PINS['relay_1'], 0)  # prepare to go backwards
    print('Setting lower threshold')
    input('Hit enter/return to begin.')
    dac.set_voltage(dac.default_val)
    input('Hit enter/return to mark absolute lower threshold')
    actuator.pos_limit_low = adc.read_adc(adc.default_channel, gain=adc.gain, data_rate=adc.sample_rate)
    dac.set_voltage(dac.stop)
    print(actuator.pos_limit_low)
    GPIO.output(PINS['relay_1'], 1)  # prepare to go forward
    print('Setting upper desired threshold')
    input('Hit enter/return  to begin.')
    dac.set_voltage(dac.default_val)
    input('Hit enter/return to mark desired upper threshold')
    actuator.pos_threshold_high = adc.read_adc(adc.default_channel, gain=adc.gain, data_rate=adc.sample_rate)
    dac.set_voltage(dac.stop)
    print(actuator.pos_threshold_high)
    GPIO.output(PINS['relay_1'], 0)  # prepare to go backwards
    print('Setting lower desired threshold')
    input('Hit enter/return  to begin.')
    dac.set_voltage(dac.default_val)
    input('Hit enter/return to mark desired lower threshold')
    actuator.pos_threshold_low = adc.read_adc(adc.default_channel, gain=adc.gain, data_rate=adc.sample_rate)
    dac.set_voltage(dac.stop)
    print(actuator.pos_threshold_low)


def set_controller():
    control_map = {1: None, 2: PController, 3: PDController, 4: PIController, 5: PIDController}
    global CONTROLLER
    spaces = ' ' * 5
    valid_choices = set(map(str, control_map.keys()))
    print('set desired controller')
    print('valid choices:')
    print(spaces + '\n{}'.format(spaces).join(['{!s}: {!s}'.format(k, getattr(v, '__name__', v))
                                               for k, v in control_map.items()]))
    choice = input('Enter controller choice: ').strip()
    while choice not in valid_choices:  # delay int conversion to handle invalid string inputs
        choice = input('Enter controller choice: ').strip()
    controller = control_map[int(choice)]
    if controller is None:
        return
    coefficients = {k: 0.0 for k in controller.coefficients}
    for coefficient in controller.coefficients:
        coefficients[coefficient] = get_k_value(coefficient)
    CONTROLLER = controller(**coefficients)


def test_configurations():
    flag = False
    print('Testing current config of:')
    print('Controller: {!s}'.format(CONTROLLER))
    print('Position Thresholds:')
    print('Absolute low: {}'.format(actuator.pos_limit_low))
    print('Absolute high: {}'.format(actuator.pos_limit_high))
    print('Set low: {}'.format(actuator.pos_threshold_low))
    print('Set High: {}'.format(actuator.pos_threshold_high))
    actuator.set_actuator_dir('forward')
    # GPIO.output(PINS['relay_1'], 1)  # set dir as forward
    dac.value = 1024
    dac.set_voltage(dac.value)
    value = adc.start_adc_comparator(adc.default_channel, 2 ** 16 - 1, 0, gain=adc.gain, data_rate=adc.sample_rate)
    while not flag:
        if value >= actuator.pos_limit_high:
            print('Hit absolute max limit', value)
            actuator.set_actuator_dir('backward')
            # GPIO.output(PINS['relay_1'], 0)
            flag = True
        # GPIO.wait_for_edge(PINS['adc_alert'], GPIO.FALLING, timeout=WAIT_TIMEOUT)
        adc.wait_for_sample(timeout=WAIT_TIMEOUT)
        value = adc.get_last_result()
    flag = False
    value = adc.get_last_result()
    while not flag:
        if value <= actuator.pos_limit_low:
            print('Hit absolute min limit', value)
            actuator.set_actuator_dir('forward')
            # GPIO.output(PINS['relay_1'], 1)
            flag = True
        # GPIO.wait_for_edge(PINS['adc_alert'], GPIO.FALLING, timeout=WAIT_TIMEOUT)
        adc.wait_for_sample(timeout=WAIT_TIMEOUT)
        value = adc.get_last_result()
    flag = False
    value = adc.get_last_result()
    while not flag:
        if value >= actuator.pos_threshold_high:
            print('Hit designated max limit', value)
            actuator.set_actuator_dir('backward')
            # GPIO.output(PINS['relay_1'], 0)
            flag = True
            # adc.stop_adc()
        # GPIO.wait_for_edge(PINS['adc_alert'], GPIO.FALLING, timeout=WAIT_TIMEOUT)
        adc.wait_for_sample(timeout=WAIT_TIMEOUT)
        value = adc.get_last_result()
    flag = False
    value = adc.get_last_result()
    while not flag:
        if value <= actuator.pos_threshold_low:
            dac.set_voltage(dac.stop)
            print('Hit designated min limit', value)
            actuator.set_actuator_dir('forward')
            # GPIO.output(PINS['relay_1'], 1)
            flag = True
        # GPIO.wait_for_edge(PINS['adc_alert'], GPIO.FALLING, timeout=WAIT_TIMEOUT)
        adc.wait_for_sample(timeout=WAIT_TIMEOUT)
        value = adc.get_last_result()
    dac.set_voltage(dac.stop)
    adc.stop_adc()


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
        5. define controller
        6. define desired actuator movement rates
        6.5. test current setup -- tweak values as wanted
        7. confirm cal data
    """
    # calibrate thresholds:
    calibrate_position()
    # set control scheme:
    set_controller()
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
def test_adc(alert_pin=adc.alert_pin, channel=adc.default_channel, sample_rate=adc.sample_rate,
             gain=adc.gain, timeout=5, **kwargs):
    abs_start = perf_counter()
    GPIO.setup(alert_pin, GPIO.IN)
    GPIO.add_event_detect(alert_pin, GPIO.FALLING, callback=diagnostic_adc_isr)
    # start = perf_counter()
    print('starting loop')
    adc.start_adc_comparator(channel, 2 ** 16 - 1, 0, gain=gain, data_rate=sample_rate)
    start_time = perf_counter()
    global LAST_TIME
    # sleep(timeout)
    while perf_counter() - start_time < timeout:
        adc.wait_for_sample(timeout=WAIT_TIMEOUT)
        # print('isr_called')
        ts = perf_counter()
        DATA.append((adc.get_last_result(), ts - LAST_TIME))
        LAST_TIME = ts
    adc.stop_adc()
    print('executed in {:6f}s:'.format(perf_counter() - abs_start))
    print('{} samples captured in {} seconds. Average of {}sps'.format(len(DATA), timeout, len(DATA) / timeout))
    return DATA


# noinspection PyUnusedLocal
def test_dac(**kwargs):
    raise NotImplementedError('dac testing not yet implemented')


# acquisition routines
# noinspection PyUnusedLocal
def monitor_adc_file(outfile, timeout, **kwargs):
    global LOGFILE
    GPIO.output(PINS['relay_2'], GPIO.LOW)  # set GPIO22 to 1/GPIO.HIGH/True
    LOGFILE = open(outfile, 'w')
    LOGFILE.write('timestamp,{}\n'.format(strftime("%Y-%m-%d %H:%M:%S")))
    GPIO.setup(adc.alert_pin, GPIO.IN)
    GPIO.add_event_detect(adc.alert_pin, GPIO.FALLING, callback=monitor_adc_isr)
    adc.start_conversions()
    # adc.start_adc_comparator(adc.default_channel, 2 ** 16 - 1, 0, gain=adc.gain, data_rate=adc.sample_rate)
    dac.set_voltage(dac.default_val)
    start_time = perf_counter()
    while perf_counter() - start_time < timeout:
        adc.wait_for_sample(timeout=WAIT_TIMEOUT)
        monitor_adc_isr(adc.alert_pin)
    # sleep(timeout)
    adc.stop_adc()
    LOGFILE.close()
    dac.set_voltage(dac.stop)


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
        cfg_formatter.dump({'POS_LIMIT_LOW': actuator.pos_limit_low,
                            'POS_LIMIT_HIGH': actuator.pos_limit_high,
                            'POS_THRESHOLD_LOW': actuator.pos_threshold_low,
                            'POS_THRESHOLD_HIGH': actuator.pos_threshold_high,
                            'SAMPLE_RATE': adc.sample_rate,
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
        arg_dict.calc_correction({'timeout': cfg['TIMEOUT'] or arg_dict['timeout'],
                         'sample_rate': cfg['adc.sample_rate'] or arg_dict['sample_rate'],
                         'outfile': cfg['OUTFILE'] or arg_dict['outfile'],
                         'units': cfg['UNITS'] or arg_dict['units'],
                         'high_max': cfg['POS_LIMIT_HIGH'] or arg_dict['high_max'],
                         'low_min': cfg['POS_LIMIT_LOW'] or arg_dict['low_min'],
                         'high_threshold': cfg['POS_THRESHOLD_HIGH'] or arg_dict['high_threshold'],
                                  'low_threshold': cfg['POS_THRESHOLD_LOW'] or arg_dict['low_threshold'],
                                  })
        adc.sample_rate = arg_dict['sample_rate']
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
        actuator.pos_limit_low = arg_dict.pop('low_min')
        actuator.pos_limit_high = arg_dict.pop('high_max')
        actuator.pos_threshold_low = arg_dict.pop('low_threshold')
        actuator.pos_threshold_high = arg_dict['high_threshold']
        if arg_dict['action'] == action_map['RESET_MIN']:
            reset_min()
        elif arg_dict['action'] == action_map['RESET_MAX']:
            reset_max()
        elif arg_dict['action'] == action_map['GOTO_POS']:
            actuator.set_position(arg_dict['position'])
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
