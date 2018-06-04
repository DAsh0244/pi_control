import time


# Import the ADS1x15 module.

import Adafruit_ADS1x15

# Import the MCP4725 module.
import Adafruit_MCP4725


import RPi.GPIO as GPIO            # import_ RPi.GPIO module

GPIO.setmode(GPIO.BCM)             # choose BCM or BOARD

from time import sleep, strftime

GPIO.setup(17, GPIO.OUT)           # set GPIO17 as an output

GPIO.setup(22, GPIO.OUT)           # set GPIO22 as an output



# Create an ADS1115 ADC (16-bit) instance.

adc = Adafruit_ADS1x15.ADS1115()

# Create a DAC instance.
dac = Adafruit_MCP4725.MCP4725()


# Choose a gain of 1 for reading voltages from 0 to 4.09V.

# Or pick a different gain to change the range of voltages that are read:

#  - 2/3 = +/-6.144V

#  -   1 = +/-4.096V

#  -   2 = +/-2.048V

#  -   4 = +/-1.024V

#  -   8 = +/-0.512V

#  -  16 = +/-0.256V

# See table 3 in the ADS1015/ADS1115 datasheet for more info on gain.

GAIN = 1



# Start continuous ADC conversions on channel 1 using the previously set gain

# value.  Note you can also pass an optional data_rate parameter, see the simpletest.py

# example and read_adc function for more infromation.

adc.start_adc(1, gain=GAIN)

# Once continuous ADC conversions are started you can call get_last_result() to

# retrieve the latest result, or stop_adc() to stop conversions.

#dac.set_voltage(0)
#dac.set_voltage(644)
#dac.set_voltage(656)
#dac.set_voltage(672)
#dac.set_voltage(688)
#dac.set_voltage(704)
#dac.set_voltage(720)
#dac.set_voltage(752)
#dac.set_voltage(768)
dac.set_voltage(1024)
#dac.set_voltage(2048)
#dac.set_voltage(3072)
#dac.set_voltage(4096)
time.sleep(0.2)

def write_value(value):
        with open("value.csv", "a") as log:
                log.write("{0},{1}\n".format(strftime("%Y-%m-%d %H:%M:%S"),str(value)))

GPIO.output(22, 0)         # set GPIO22 to 1/GPIO.HIGH/True


# Read channel 0 for 5 seconds and print out its values.

print('Reading ADS1x15 channel 0 for 1800 seconds...')

start = time.time()

while (time.time() - start) <= 1800.0: # Read the last ADC conversion value and print it out.

    value = adc.get_last_result()

    print('Channel 1: {0}'.format(value))

    if (value <= 750):

        GPIO.output(17, 1)

        sleep(0.05)

        write_value(value)

    elif (value >= 17800):

        GPIO.output(17, 0)

        sleep(0.05)

        write_value(value)

    else:

        sleep (0.05)

print('Go to the start position')

while (value > 750): # Read the last ADC conversion value and print it out.

        value = adc.get_last_result()

        print('Channel 1: {0}'.format(value))

        GPIO.output(17, 0)

        sleep(0.05)


GPIO.cleanup()                 # resets all GPIO ports used by this program

# Stop continuous conversion.  After this point you can't get data from get_last_result!

adc.stop_adc()
dac.set_voltage(0)

