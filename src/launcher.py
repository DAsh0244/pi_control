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

import orchestration
from launch import parser

if __name__ == '__main__':
    args = parser.parse_args()
    recipe = orchestration.load_procedure(args.path)
    executor = orchestration.ProcedureExecutor(config=recipe['CONFIG'], routines=recipe['ROUTINES'])
