#! /usr/bin/env python3

# TODO: check if refactor works

from collections import deque
from time import strftime, perf_counter  # , sleep

from actions import actions
from launch import parser, cmds
from libs.utils import load_config
from actions.calibrate import calibrate
from libs.hal import (
    adc,
    dac,
    PINS,
    GPIO,
    actuator,
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
        calibrate(interface=actuator, params={}, nxt=None)
    elif arg_dict['cmd'] == cmds['TEST_POS']:
        actuator.pos_limit_low = arg_dict.pop('low_min')
        actuator.pos_limit_high = arg_dict.pop('high_max')
        actuator.pos_threshold_low = arg_dict.pop('low_threshold')
        actuator.pos_threshold_high = arg_dict['high_threshold']
        if arg_dict['action'] == actions['RESET_MIN']:
            actuator.reset_min()
        elif arg_dict['action'] == actions['RESET_MAX']:
            actuator.reset_max()
        elif arg_dict['action'] == actions['GOTO_POS']:
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
