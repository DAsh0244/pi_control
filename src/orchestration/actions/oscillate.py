"""
pi_control
oscillate.py
Author: Danyal Ahsanullah
Date: 6/28/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: 
"""

import sys
from libs.utils import INF
from libs.hal import actuator, hal_init
from time import perf_counter


def oscillate(interface=actuator, params=None):
    """
    Moves from thresholds described in params dict with keys of 'low_pos', 'high_pos'.
    Movement speed is optionally defined in params dict with the 'speed' key.
    Frequency can be optionally defined in Hz with the 'freq' key. It will overwrite any value taken from the speed key.
    Adaptive controller is optionally specified with the 'controller' key.
    The ability to end oscillation at the closest threshold (low or high) is available with the 'reset_closest' key,
        which expects a boolean True or False value. If not specified, defaults to False
    Mutually exclusive number of oscillations and timeout are also optional params. if both are specified,
    it will stop at whatever comes first.
        - timeout is specified with the 'timeout' key and expects a float, defaults to inf
        - repetitions is specified with the 'repetitions' key and expects an int, defaults to inf

    depending on the conditions, four possible return values are possible plus an error condition:
        - 'timeout_stopped'  - broke on a timeout and left actuator where it was
        - 'repeats_stopped'  - broke on a repeat and left actuator where it was
        - 'timeout_reset'    - broke on a timeout and reset actuator to closest boundary point
        - 'repeats_reset'    - broke on a timeout and reset actuator to closest boundary point
        - 'error'            - triggers on any failure during oscillations
    """
    hal_init()
    condition = 'stopped'
    low_pos = params['low_pos']
    high_pos = params['high_pos']
    timeout = params.get('timeout', INF)
    repetitions = params.get('repetitions', INF)
    controller = params.get('controller', None)
    old_speed = interface.speed_controller.default_val
    speed = params.get('speed', interface.speed_controller.default_val)
    if params.get('freq', None) is not None:
        # calculate new speed for desired frequency
        pass
    interface.speed_controller.default_val = speed
    interface.mount_controller(controller)
    repeats = 0
    start = perf_counter()
    try:
        while (repeats < repetitions) and ((perf_counter() - start) < timeout):
            print('start oscillation', (perf_counter() - start))
            interface.set_position(low_pos)
            interface.set_position(high_pos)
            repeats += 1
            print('next oscillation')
        if params.get('reset_closest', False):
            condition = 'reset'
            # is closer to lower spot than higher spot
            if abs(interface.position - low_pos) > abs(interface.position - high_pos):
                interface.set_position(low_pos)
            else:
                interface.set_position(high_pos)
        interface.speed_controller.default_val = old_speed
        return '_'.join(('timeout' if repeats < repetitions else 'repeats', condition))
    except Exception as e:
        interface.set_out_speed(interface.speed_controller.stop)
        interface.speed_controller.default_val = old_speed
        sys.stderr.write(str(e))
        sys.stderr.write('\n')
        sys.stderr.write(str(sys.exc_info()))
        sys.stderr.flush()
        return 'error'
