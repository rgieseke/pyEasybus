# -*- coding: utf-8 -*-

"""
Python Interface for Easybus Devices.

2010-2011 Robert Gieseke - robert.gieseke@gmail.com
See LICENSE

Example usage:

    from easybus import Easybus
    thermometer = Easybus('COM1')
    print thermometer.value()
"""

import serial

class Easybus(serial.Serial):
    def __init__(self, com_port):
        """
        Initialise EASYBUS device.

            Example:
            thermometer = Easybus('COM1')
        """
        serial.Serial.__init__(self, com_port)
        self.baudrate = 4800
        self.bytesize = serial.EIGHTBITS
        self.parity = serial.PARITY_NONE
        self.stopbits = serial.STOPBITS_ONE
        self.timeout = 1
        self.error_msg = {16352: 'Error 1: measuring range overrun',
                          16353: 'Error 2: measuring range underrun',
                          16362: 'Error 11: calculation not possible',
                          16363: 'Error 7: system error',
                          16364: 'Error 8: battery empty',
                          16365: 'Error 9: sensor defective',
                         }
        self.unit_nrs = {1: u'°C',
                         2: u'°F',
                         3: 'K',
                         10: '% r.F',
                         20: 'bar',
                         21: 'mbar',
                         22: 'Pascal',
                         23: 'hPascal',
                         24: 'kPascal',
                         25: 'MPascal',
                         27: 'mmHg',
                         28: 'PSI',
                         29: 'mm H2O',
                         30: 'S/cm',
                         31: 'ms/cm',
                         32: 'uS/cm',
                         40: 'ph',
                         42: 'rH',
                         45: 'mg/l O2',
                         46: '% Sat O2',
                         50: 'U/min',
                         53: 'Hz',
                         55: 'Impuls(e)',
                         60: 'm/s',
                         61: 'km/h',
                         70: 'mm',
                         71: 'm',
                         72: 'inch',
                         73: 'ft',
                         80: 'l/h',
                         81: 'l/min',
                         82: 'm^3/h',
                         83: 'm^3/min',
                         90: 'g',
                         91: 'kg',
                         92: 'N',
                         93: 'Nm',
                         100: 'A',
                         101: 'mA',
                         105: 'V',
                         106: 'mV',
                         107: 'uV',
                         111: 'W',
                         112: 'kW',
                         115: 'Wh',
                         116: 'kWh',
                         119: 'Wh/m2',
                         120: 'mOhm',
                         121: 'Ohm',
                         122: 'kOhm',
                         123: 'MOhm',
                         125: 'kohm/cm',
                         150: '%',
                         151: u'°',
                         152: 'ppm',
                         160: 'g/kg',
                         170: 'kJ/kg',
                         171: 'kcal/kg',
                         175: 'dB',
                         176: 'dBm',
                         177: 'dBA',
                        }

    def channel(self, address):
        """
        Return address byte.
        """
        # address needs to be inverted
        # Ch. 1 => 254, 2 => 253, ...
        return ~address & 0xFF

    def crc(self, byte1, byte2):
        """
        Return crc byte. (Byte 2, 5, 8, ...)
        """
        helper = (byte1 << 8) + byte2
        for i in range(16):
            if (helper & 0x8000):
                helper = (helper << 1) ^ 0x700
            else:
                helper = helper << 1
        helper = helper >> 8
        return ~helper & 0xff

    def value(self, address=1):
        """
        Return displayed measuring value.
        """
        command = 0
        byte0 = self.channel(address)
        crc_byte = self.crc(byte0, command)
        request = chr(byte0) + chr(command) + chr(crc_byte)
        self.write(request)
        response = self.read(6)
        if response == '':
            return "Error: No value read."
        byte3 = int(response[3].encode('hex'), 16)
        byte4 = int(response[4].encode('hex'), 16)
        int_value = (16383 & ((256 * (255 - byte3)) + byte4)) - 2048
        if int_value >= 16532:
            return self.error_msg(int_value)
        dec_point = 49152 & (256 * (255 - byte3))
        if dec_point == 49152:
            temp_value = int_value * 10**-3
        elif dec_point == 32768:
            temp_value = int_value * 10**-2
        elif dec_point == 16384:
            temp_value = int_value * 10**-1
        elif dec_point == 0:
            temp_value = int_value
        else:
            temp_value = False
        return temp_value

    def display_unit(self, address=1):
        """
        Return display unit as a string.
        """
        byte0 = self.channel(address)
        byte1 = 242
        byte3 = 53
        byte4 = 0
        crc_byte_2 = self.crc(byte0, byte1)
        crc_byte_5 = self.crc(byte3, byte4)
        request = "".join([chr(item) for item in [byte0, byte1, crc_byte_2,
                                                  byte3, byte4, crc_byte_5]])
        self.write(request)
        response = self.read(9)
        highbyte = int(response[6].encode('hex'), 16)
        lowbyte = int(response[7].encode('hex'), 16)
        int_dat = 0
        int_dat = int_dat | (highbyte ^ 255)
        int_dat = int_dat << 8
        int_dat = int_dat | lowbyte
        return self.unit_nrs[int_dat]
