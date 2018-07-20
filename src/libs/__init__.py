#! /usr/bin/env python
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
pi_control
libs/__init__.py
Author: Danyal Ahsanullah
Date: 6/11/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: 
"""

try:
    from .max31856 import MAX31856
except ImportError:
    import warnings as _warnings
    from .utils import warning_on_one_line

    _warnings.formatwarning = warning_on_one_line
    _warnings.warn('failed to import MAX31856 interface', RuntimeWarning)
# import utils
