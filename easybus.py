"""
Python Interface for Easybus Devices.

2010-2011 Robert Gieseke - robert.gieseke@gmail.com
2022 Christian Sadeler (Update to Python 3)

Contains conversion code from pyeasyb
(https://github.com/TheUncleKai/pyeasyb)
Copyright (C) 2017, Kai Raphahn <kai.raphahn@laburec.de>

See LICENSE

Tested with GMH3750 thermometer, Python 3.9.7 and pySerial 3.5

Example usage:

    from easybus import Easybus
    thermometer = Easybus('COM4')
    print(thermometer.value())
    print(thermometer.display_unit())
"""

import serial
import sys


class Easybus(serial.Serial):
    def __init__(self, com_port):
        """
        Initialise EASYBUS device.

            Example:
            thermometer = Easybus('COM4')
        """
        serial.Serial.__init__(self, com_port)
        self.baudrate = 4800
        self.bytesize = serial.EIGHTBITS
        self.parity = serial.PARITY_NONE
        self.stopbits = serial.STOPBITS_ONE
        self.timeout = 1
        self.error_msg = {
            16352: "Error 1: measuring range overrun",
            16353: "Error 2: measuring range underrun",
            16362: "Error 11: calculation not possible",
            16363: "Error 7: system error",
            16364: "Error 8: battery empty",
            16365: "Error 9: sensor defective",
        }
        self.unit_nrs = {
            1: u"°C",
            2: u"°F",
            3: "K",
            10: "% r.F",
            20: "bar",
            21: "mbar",
            22: "Pascal",
            23: "hPascal",
            24: "kPascal",
            25: "MPascal",
            27: "mmHg",
            28: "PSI",
            29: "mm H2O",
            30: "S/cm",
            31: "ms/cm",
            32: "uS/cm",
            40: "ph",
            42: "rH",
            45: "mg/l O2",
            46: "% Sat O2",
            50: "U/min",
            53: "Hz",
            55: "Impuls(e)",
            60: "m/s",
            61: "km/h",
            70: "mm",
            71: "m",
            72: "inch",
            73: "ft",
            80: "l/h",
            81: "l/min",
            82: "m^3/h",
            83: "m^3/min",
            90: "g",
            91: "kg",
            92: "N",
            93: "Nm",
            100: "A",
            101: "mA",
            105: "V",
            106: "mV",
            107: "uV",
            111: "W",
            112: "kW",
            115: "Wh",
            116: "kWh",
            119: "Wh/m2",
            120: "mOhm",
            121: "Ohm",
            122: "kOhm",
            123: "MOhm",
            125: "kohm/cm",
            150: "%",
            151: u"°",
            152: "ppm",
            160: "g/kg",
            170: "kJ/kg",
            171: "kcal/kg",
            175: "dB",
            176: "dBm",
            177: "dBA",
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
            if helper & 0x8000:
                helper = (helper << 1) ^ 0x700
            else:
                helper = helper << 1
        helper = helper >> 8
        return ~helper & 0xFF

    def value(self, address=1):
        """
        Return displayed measuring value.
        """

        def decode_u16(bytea: int, byteb: int) -> int:
            data = (255 - bytea) << 8
            data = data | byteb
            return data

        def decode_u32(inputa: int, inputb: int) -> int:
            data = (inputa << 16) | inputb
            return data

        def crop_u32(value: int) -> int:
            size = sys.getsizeof(value)
            result = value

            if size > 32:
                result = value & 0x00000000FFFFFFFF
            return result

        def to_signed32(value):
            value = value & 0xFFFFFFFF
            return (value ^ 0x80000000) - 0x80000000

        command = 0
        byte0 = self.channel(address)
        crc_byte = self.crc(byte0, command)
        request = (byte0, command, crc_byte)
        self.write(request)
        response = self.read(9)
        if response == "":
            return "Error: No value read."
        byte3, byte4 = response[3], response[4]
        byte6, byte7 = response[6], response[7]
        u16_integer1 = decode_u16(byte3, byte4)
        u16_integer2 = decode_u16(byte6, byte7)
        u32_integer = decode_u32(u16_integer1, u16_integer2)

        float_pos = 0xFF - byte3
        float_pos = (float_pos >> 3) - 15

        u32_integer = crop_u32(u32_integer & 0x07FFFFFF)

        if (100000000 + 0x2000000) > u32_integer:
            compare = crop_u32(u32_integer & 0x04000000)

            if 0x04000000 == compare:
                u32_integer = crop_u32(u32_integer | 0xF8000000)

            u32_integer = crop_u32(u32_integer + 0x02000000)
        else:
            error_num = u32_integer - 0x02000000 - 100000000
            return self.error_msg(error_num)

        i32_integer = to_signed32(u32_integer)
        temp_value = float(i32_integer) / float(float(10.0) ** float_pos)

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
        request = (byte0, byte1, crc_byte_2, byte3, byte4, crc_byte_5)
        self.write(request)
        response = self.read(9)
        highbyte = response[6]
        lowbyte = response[7]
        int_dat = 0
        int_dat = int_dat | (highbyte ^ 255)
        int_dat = int_dat << 8
        int_dat = int_dat | lowbyte
        return self.unit_nrs[int_dat]
