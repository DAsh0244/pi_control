from sys import platform as _platform

GLOBAL_VCC = 3.3
TIMEOUT = None
UNITS = 'raw'
OUTFILE = None
LOAD_CELL_PORT = 'COM10' if _platform == 'win32' else '/dev/ttyusb0'
PINS = {
    'relay_1': 17,
    'relay_2': 22,
    'adc_alert': 21,
}
