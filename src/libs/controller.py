# controller.py
# contains definitions for the various controllers and control logic
#
# usage:
# import controller
# ...
# controller = PIDController
# within actions, use the controller as such
#
# done = False
# def get_input():
#     return adc.level2voltage(adc.read_single())
# def scale_output(outval):
#     return dac.voltage2level(outval)
# ctrl = controller(<kp>...<kn>, input_func=get_input, output_func=scale_output)
# ctrl.ref = target
# while abs(target.position - get_input()) > target.error:
#     ctrl.process()
#

from time import perf_counter
from abc import ABC, abstractmethod
from typing import Callable, Iterable, Union


class ControllerBase(ABC):
    coefficients = ''

    def __init__(self, input_func: Callable[[], Union[Iterable, float]],
                 output_func: Callable[[Union[float, int]], None], desired_reference: float = 0.0):
        """
        :param input_func: function that is used to query the system, and get the new set of inputs.
                           Input mappings should be applied here
        :param output_func: function that can be used to translate the calculated output to a more appropriate mapping.
        :param desired_reference: default reference for the controller to try and achieve.
                                  To mutate the reference value, simply assign to the 'ref' attribute
        """
        self.get_input = input_func
        self.send_output = output_func
        self.input = input_func()
        self.ref = desired_reference
        self.out = 0.0
        self.last_time = perf_counter()
        self.last_err = 0.0
        self.err = self.ref - self.input

    @abstractmethod
    def calc_correction(self, time_val):
        return 0.0

    def process(self):
        self.input = self.get_input()
        self.err = self.ref - self.input
        self.out = self.calc_correction(perf_counter())
        self.send_output(self.out)


class PController(ControllerBase):
    coefficients = 'p'

    def __init__(self, kp, *args, **kwargs):
        self.kp = kp
        super().__init__(*args, **kwargs)

    def calc_correction(self, time_val):
        return self.err * self.kp


class PDController(ControllerBase):
    coefficients = 'pd'

    def __init__(self, kp, kd, *args, **kwargs):
        self.kp = kp
        self.kd = kd
        super().__init__(*args, **kwargs)

    def calc_correction(self, time_val):
        p_correction = self.err * self.kp
        d_correction = self.kd * (self.err - self.last_err) / (time_val - self.last_time)
        self.last_time = time_val
        return p_correction + d_correction


class PIController(ControllerBase):
    coefficients = 'pi'

    def __init__(self, kp, ki, *args, **kwargs):
        self.kp = kp
        self.ki = ki
        self.acc = 0
        super().__init__(*args, **kwargs)

    def calc_correction(self, time_val):
        self.acc += self.err * time_val
        p_correction = self.err * self.kp
        i_correction = self.acc * self.ki
        return p_correction + i_correction


class PIDController(ControllerBase):
    coefficients = 'pid'

    def __init__(self, kp, ki, kd, *args, **kwargs):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.acc = 0
        super().__init__(*args, **kwargs)

    def calc_correction(self, time_val):
        self.acc += self.err * time_val
        p_correction = self.err * self.kp
        d_correction = (self.err - self.last_err) / (time_val - self.last_time) * self.kd
        i_correction = self.acc * self.ki
        self.last_time = time_val
        # print('correction', p_correction, i_correction, d_correction)
        return p_correction + i_correction + d_correction
