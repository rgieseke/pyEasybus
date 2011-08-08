# Python Interface for Easybus Devices.

2010-2011 Robert Gieseke - robert.gieseke@gmail.com

MIT license, see LICENSE.

### Example usage:

    from easybus import Easybus
    thermometer = Easybus('COM1')
    print thermometer.value()

### Requirements:
pySerial - <http://pyserial.sourceforge.net/>

### Note:
Note that this has only been tested with Easybus connected thermometers,
however, other units are already included, making it easy to extend for other
Easybus devices.

### Manual for check-sum code:
"EASYBUS Schnittstelle ohne DLL, 12.12.2007" (German)
<http://www.greisinger.de/files/upload/de/downloads/dokumente/EASYBUS%20Schnittstelle%20ohne%20DLL.pdf>

E.A.S.Y.Bus and the EASYBus Logo is a trademark or registered trademark of GREISINGER electronic GmbH.
