# controller.py
# contains definitions for the various controllers and control logic
#
# usage:
# from controller import control_map
# ...
# controller = control_map[<controller_index>]

from abc import ABC, abstractmethod
from collections import deque, namedtuple

Point = namedtuple('Point', 'time error')


class ControllerBase(ABC):
    def __init__(self, input_func: function, output_func: function, desired_reference: float = 0.0,
                 history_len: int = 20):
        """
        :param input_func: function that is used to query the system, and get the new set of inputs.
                           Input mappings should be applied here
        :param output_func: function that can be used to translate the calculated output to a more appropriate mapping.
        :param desired_reference: default reference for the controller to try and achieve.
                                  To mutate the reference value, simply assign to the 'ref' attribute
        """
        self.history = deque(maxlen=history_len)
        self.get_input = input_func
        self.send_output = output_func
        self.out = 0
        self.input = input_func()
        self.ref = desired_reference
        self.err = 0  # safer to start from 0

    @abstractmethod
    def process(self, time_val):
        self.err = self.ref - self.input
        self.history.append(Point(time_val, self.err))

    def update(self, time_val):
        self.input = self.get_input()
        self.process(time_val)
        self.send_output(self.out)


class PController(ControllerBase):
    def __init__(self, kp, *args, **kwargs):
        self.kp = kp
        super().__init__(*args, **kwargs)

    def process(self, time_val):
        super().process(time_val)
        self.out = self.err * self.kp


class PDController(ControllerBase):
    def __init__(self, kp, kd, *args, **kwargs):
        self.kp = kp
        self.kd = kd
        super().__init__(*args, **kwargs)

    def process(self, time_val):
        super().process(time_val)
        last_state = self.history[-2]  # -1 b/c super call appends to history
        p_correction = self.err * self.kp
        d_correction = (self.err - last_state.error) / (time_val - last_state.time) * self.kd
        self.out = p_correction + d_correction


class PIController(ControllerBase):
    def __init__(self, kp, ki, *args, **kwargs):
        self.kp = kp
        self.ki = ki
        self.acc = 0
        super().__init__(*args, **kwargs)

    def process(self, time_val):
        super().process(time_val)
        self.acc += self.err * time_val
        p_correction = self.err * self.kp
        i_correction = self.acc * self.ki
        self.out = p_correction + i_correction


class PIDController(ControllerBase):
    def __init__(self, kp, ki, kd, *args, **kwargs):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.acc = 0
        super().__init__(*args, **kwargs)

    def process(self, time_val):
        super().process(time_val)
        self.acc += self.err * time_val
        last_state = self.history[-2]  # -1 b/c super call appends to history
        p_correction = self.err * self.kp
        d_correction = (self.err - last_state.error) / (time_val - last_state.time) * self.kd
        i_correction = self.acc * self.ki
        self.out = p_correction + i_correction + d_correction


CONTROL_MAP = {1: None, 2: PController, 3: PDController, 4: PIController, 5: PIDController}
