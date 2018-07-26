#! /usr/bin/env python
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
pi_control
pi_control.py
Author: Danyal Ahsanullah
Date: 7/24/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: main launcher file for the stack.
"""

from libs.hal import hal_cleanup, actuator
import orchestration
from launch import parser

if __name__ == '__main__':
    args = parser.parse_args()
    recipe = orchestration.load_procedure(args.config)
    actuator.pos_limit_low = recipe['CONFIG']['lower_limit']
    actuator.pos_limit_high = recipe['CONFIG']['upper_limit']
    executor = orchestration.ProcedureExecutor(cfg=recipe['CONFIG'], routines=recipe['ROUTINES'])
    try:
        executor.run()
    except KeyboardInterrupt:
       hal_cleanup()

