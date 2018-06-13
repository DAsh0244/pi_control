#! /usr/bin/env python3

# Copyright (c) 2016 John Robinson
# Author: John Robinson
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# Global Imports
# import logging
# import time
import Adafruit_GPIO

# Local Imports
from libs import MAX31856

# import time, math
from time import sleep, strftime

import matplotlib.pyplot as plt

plt.ion()
x_time = []
sensor_internal = []
sensor_external = []
sensor2_internal = []
sensor2_external = []
sensor3_internal = []
sensor3_external = []

# Uncomment one of the blocks of code below to configure your Pi to use software or hardware SPI.

# Raspberry Pi software SPI configuration.
# software_spi = {"clk": 13, "cs": 5, "do": 19, "di": 26}
# sensor = MAX31856(software_spi=software_spi)

# software_spi2 = {"clk": 13, "cs": 6, "do": 19, "di": 26}
# sensor2 = MAX31856(software_spi=software_spi2)

# Raspberry Pi hardware SPI configuration.
SPI_PORT = 0
SPI_DEVICE = 0
sensor = MAX31856(avgsel=4, hardware_spi=Adafruit_GPIO.SPI.SpiDev(SPI_PORT, SPI_DEVICE))

SPI_PORT = 0
SPI_DEVICE = 1
sensor2 = MAX31856(avgsel=4, hardware_spi=Adafruit_GPIO.SPI.SpiDev(SPI_PORT, SPI_DEVICE))

sensor3 = MAX31856(avgsel=4, software_spi={'clk': 13, 'cs': 5, 'do': 19, 'di': 26})


def write_temp(timestamp, temp, internal, temp2, internal2, temp3, internal3):
    with open("temp.csv", "a") as log:
        log.write("{0},{1!s},{2!s},{3!s},{4!s},{5!s},{6!}\n".format(timestamp,
                                                                    temp, internal,
                                                                    temp2, internal2,
                                                                    temp3, internal3
                                                                    )
                  )


def graph():
    plt.clf()
    # plt.scatter(x,y,y2)
    plt.plot(x_time,
             sensor_external, sensor_internal,
             sensor2_external, sensor2_internal,
             sensor3_external, sensor3_internal)
    plt.pause(0.0001)


print('Press Ctrl-C to quit.')
while True:
    time_stamp = strftime("%Y-%m-%d %H:%M:%S")
    temp = sensor.read_temp_c()
    internal = sensor.read_internal_temp_c()
    temp2 = sensor2.read_temp_c()
    internal2 = sensor2.read_internal_temp_c()
    temp3 = sensor3.read_temp_c()
    internal3 = sensor3.read_internal_temp_c()

    x_time.append(time_stamp)
    sensor_internal.append(internal)
    sensor_external.append(temp)
    sensor2_internal.append(internal2)
    sensor2_external.append(temp2)
    sensor3_internal.append(internal3)
    sensor3_external.append(temp3)

    print('Thermocouple Temperature1: {0:0.3F}*C'.format(temp))
    print('    Internal Temperature1: {0:0.3F}*C'.format(internal))
    print('Thermocouple Temperature2: {0:0.3F}*C'.format(temp2))
    print('    Internal Temperature2: {0:0.3F}*C'.format(internal2))
    print('Thermocouple Temperature3: {0:0.3F}*C'.format(temp3))
    print('    Internal Temperature3: {0:0.3F}*C'.format(internal3))

    # time.sleep(1.0)

    write_temp(time_stamp, temp, internal, temp2, internal2, temp3, internal3)
    graph()
    sleep(0.1)
