# controller.py
# contains definitions for the various controllers and control logic
#
# usage:
# from controller import control_map
# ...
# controller = control_map[<controller_index>]

from abc import ABC, abstractmethod


class ControllerBase(ABC):
    def __init__(self, input_func, output_func, output_map, input_map, desired_reference=0):
        self.get_input = input_func
        self.in_map = input_map
        self.send_output = output_func
        self.out_map = output_map
        self.out = 0
        self.input = input_func()
        self.ref = desired_reference
        self.err = 0  # safer to start from 0

    @abstractmethod
    def process(self, delta_t):
        raise NotImplemented('Should be impemented by subclass')

    def update(self, time_step):
        self.input = self.get_input()
        self.process(time_step)
        self.send_output(self.out)


class ProportionalController(ControllerBase):
    def __init__(self, kp, *args, **kwargs):
        self.kp = kp
        super().__init__(*args, **kwargs)

    def process(self, delta_t):
        self.input = self.get_input()
        error = self.ref - self.out


class ProportionalDifferentialController(ControllerBase):
    def __init__(self, kp, kd, *args, **kwargs):
        self.kp = kp
        self.kd = kd
        super().__init__(*args, **kwargs)

    def process(self, delta_t):
        pass


# PControl = ProportionalController
# PDControl = ProportionalDifferentialController
CONTROL_MAP = {1: None, 2: ProportionalController, 3: ProportionalDifferentialController}
