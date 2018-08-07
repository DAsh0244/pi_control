#! /usr/bin/env/python3.6

import re
import sys
from time import sleep
from serial import Serial

# regex test:
# http://www.pyregex.com/?id=eyJyZWdleCI6IlJlYWRpbmc6IFxcWyg%2FUDxtYXNzPi0%2FXFxkK1xcLlxcZCspXFxzKD9QPHVuaXRzPlxcdyspXFxdXFxzK0NhbGlicmF0aW9uIEZhY3RvcjpcXHMoP1A8ZmFjdG9yPi0%2FXFxkKykiLCJmbGFncyI6MTAsIm1hdGNoX3R5cGUiOiJmaW5kYWxsIiwidGVzdF9zdHJpbmciOiJSZWFkaW5nOiBbMS4yMzQ1IGxic10gICBDYWxpYnJhdGlvbiBGYWN0b3I6IDEyMzQ1Njc4XG5SZWFkaW5nOiBbLTIuMzQ1NSBrZ10gICBDYWxpYnJhdGlvbiBGYWN0b3I6IC0xMjM0NSJ9
pattern = re.compile(r'Reading: \[(?P<mass>-?\d+\.\d+)\s(?P<units>\w+)\]\s+Calibration Factor:\s(?P<factor>-?\d+)')


def calibrate_load_cell(desired_value, tolerance=0.001):
    # open the interface
    interface = Serial('/dev/ttyUSB0')
    # open menu
    interface.write(b'x')
    interface.reset_input_buffer()
    sleep(2)  # waits for the device to finish printing
    # select calibrate
    interface.write(b'2')
    #  Serial.println(F("Scale calibration"));
    #  Serial.println(F("Remove all weight from scale"));
    #  Serial.println(F("After readings begin, place known weight on scale"));
    #  Serial.println(F("Press + or a to increase calibration factor"));
    #  Serial.println(F("Press - or z to decrease calibration factor"));
    #  Serial.println(F("Press 0 to zero factor"));
    #  Serial.println(F("Press x to exit"));
    for i in range(0, 7):  # toss first 7 lines
        interface.readline()
    reading = interface.readline().decode('utf-8')
    parsed_reading = pattern.match(
        reading).groupdict()  # returns a dict in the form {'mass': '<measured_mass>', 'units': '<parsed_units>', 'factor':'<calibration_factor>'}
    mass, units, factor = float(parsed_reading['mass']), parsed_reading['units'], int(parsed_reading['factor'])
    # calculate error
    error = desired_value - mass

    if error < tolerance:  # spot on to begin with
        return
    else:
        while error > tolerance:
            if error < 0:  # too far -- should decrease cal factor
                interface.write('-')
            elif error > 0:  # too short -- should increase cal factor
                interface.write('+')
            reading = interface.readline().decode('utf-8')
            parsed_reading = pattern.match(
                reading).groupdict()  # returns a dict in the form {'mass': '<measured_mass>', 'units': '<parsed_units>', 'factor':'<calibration_factor>'}
            mass, units, factor = float(parsed_reading['mass']), parsed_reading['units'], int(parsed_reading['factor'])
            # calculate error
            error = desired_value - mass


if __name__ == '__main__':
    tolerance = 0.001
    if len(sys.argv) == 1:  # no extra args were supplied
        desired_value = float(input('enter the calibration mass').strip())
    else:  # command line args were supplied, assume first arguement supplied is desired calibration weight
        desired_value = float(sys.argv[1])  # arg 0 is the name of the script
        try:  # if its there take tolerance
            tolerance = float(sys.argv[2])
        except IndexError:
            pass
    calibrate_load_cell(desired_value, tolerance)
