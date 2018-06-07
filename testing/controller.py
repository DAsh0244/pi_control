# controller.py
# contains definitions for the various controllers and control logic
#
# usage:
# from controller import control_map
# ...
# controller = control_map[<controller_index>]

from abc import ABC, abstractmethod

class ControllerBase(ABC):
    def __init__(input_func, output_func, output_map, input_map, desired_reference=0):
        self.get_input = input_func
        self.in_map = input_map
        self.send_output = output_func
        self.out_map = output_map
        self.out = 0
        self.input = input_func()
        self.ref = desired_reference
        self.err = 0  # safer to start from 0

    @abstractmethod
    def process():
        raise NotImplemented('Should be impemented by subclass')

    def update(timestep):
        self.input = self.get_input()
        self.process(timestamp)
        self.send_output(self.out)


class ProportionalController(ControllerBase):
    def __init__(Kp, *args, **kwargs):
        self.kp = Kp
        super().__init__(*args,**kwargs)

    def process():
        self.input = self.get_input()
        error = self.ref - self.out


class ProportionalDifferentialController(ControllerBase):
    def __init__(Kp, Kd, *args, **kwargs):
            self.kp = Kp
            self.kd = Kd
            super().__init__(*args,**kwargs)

    def process():
        pass

# PControl = ProportionalController
# PDControl = ProportionalDifferentialController

CONTROL_MAP = {1: None, 2:ProportionalController, 3:ProportionalDifferentialController}