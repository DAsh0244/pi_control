#! /usr/bin/env python3
"""
ball park estimations for the actuator control system


"""

from argparse import ArgumentParser

try:
    import matplotlib.pyplot as plt
    PLOT = True
except ImportError:
    PLOT = False

parser = ArgumentParser()
parser.add_argument('-a', '--accuracy', action='store', default=0.00393701, help='desired accuracy of the system')

def mm2in(mmlength):
    return mmlength * 0.0393701

def in2mm(inlength):
    return inlength * 25.4

def lbs2kg(lbs):
    return lbs * 0.453592

def kg2lbs(kg):
    return kg * 2.20462

DESIRED_ACC = mm2in(0.1)

# A/D parameters
# Valid values are: 8, 16, 32, 64, 128, 250, 475, 860 -- default is 128sps
ADC_SAMPLE_RATE = 128
ADC_BITS = 16
ADC_MAP = {2/3 : 6.144,
                     1 : 4.096,
                     2 : 2.048,
                     4 : 1.024,
                     8 : 0.512,
                     16 : 0.256,
                    }
ADC_POLARITY = 1  # 1 for positive rail, -1 for negative rail
ADC_GAIN = 1
ADC_MAX_VOLTAGE = ADC_POLARITY * ADC_MAP[ADC_GAIN]
ADC_STEP_SIZE = abs(ADC_MAX_VOLTAGE / (2**ADC_BITS))  # volt/step
ADC_RESPONSE_TIME = 1/ADC_SAMPLE_RATE

# potentiometer parameters
POT_VOLTAGE = 3.3
POT_RESTISTANCE = 10000

# actuator  information
STROKE = 12
ACTUATOR_INCHES_PER_SECOND = {35:{'None':2.00,
                                                                    'Full':1.38},
                                                            50:{'None':1.14,
                                                                   'Full':0.83},
                                                            150:{'None':0.37,
                                                                     'Full':0.28},
                                                            }

# take worst case actuator speed:
move_rate = min(load['None'] for load in ACTUATOR_INCHES_PER_SECOND.values())
print('ADC_LATENCY (s):')
print('Sample Rate (sps) | System Latency (s) | Data Rate (bps) | Move Precision (mm)')
for sample_rate in (8, 16, 32, 64, 128, 250, 475, 860):
    print('{:^17} | {:^18.6f} | {:^15} | {:^10.6f}'.format(sample_rate, 1/sample_rate, 16*sample_rate, in2mm(move_rate)/sample_rate))
print('')

print('Load force and response rate: ')
for load, types in ACTUATOR_INCHES_PER_SECOND.items():
    print('load force (lbs): {}'.format(load))
    # print('load force (kg): {}'.format(lbs2kg(load)))
    print('Load Type | Speed (in/s) | Min Response Time (s)')
    # print('Load Type | Speed (mm/s) | Min Response Time (s)')
    for load_type,rate in types.items():
        print('{:^10}|{:^14}|{:^25.6f}'.format(load_type, rate, DESIRED_ACC/rate))
        # print('{:^10}|{:^14}|{:^25}'.format(load_type, in2mm(rate), in2mm(DESIRED_ACC/rate)))
    print('')

print('stroke distance check (bars around actual stroke length):')
# print('Stroke (in) | Detectable Distance (in) | Meets Spec | Safety Margin')
print('Stroke (mm) | Detectable Distance (mm) | Meets Spec | Safety Margin')
print('+'.join(['-'*12, '-'*26, '-'*12, '-'*12]))
for stroke in range(10,25+1):
    distance_per_volt = stroke / POT_VOLTAGE
    detectable_distance = ADC_STEP_SIZE * distance_per_volt
    if stroke == STROKE:
        print('+'.join(['-'*12, '-'*26, '-'*12, '-'*12]))
    print('{:^12.6f}|{:^26.6G}|{:^12}|{:^12}'.format(\
                                                                    # stroke,
                                                                    # detectable_distance,
                                                                    in2mm(stroke),
                                                                    in2mm(detectable_distance),
                                                                    repr(detectable_distance<DESIRED_ACC),
                                                                    repr((detectable_distance*10)<DESIRED_ACC)
                                                                     )
             )
    if stroke == STROKE:
        print('+'.join(['-'*12, '-'*26, '-'*12, '-'*12]))
print('')
