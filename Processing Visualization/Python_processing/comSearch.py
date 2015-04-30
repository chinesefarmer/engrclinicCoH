import sys
import serial
from serial.tools import list_ports

class TeensySerial:
    def __init__(self, baudrate):
        self.teensy_port = self.getTeensyPort()
        self.teensy = serial.Serial(self.teensy_port[0], baudrate)

    def getTeensyPort(self):
        """Discover where is Teensy."""
        ports_avaiable = list(list_ports.comports())
        teensy_port = tuple()
        for port in ports_avaiable:
            if port[1].startswith("Teensy"):
                teensy_port = port
        if teensy_port:
            return teensy_port

    def close(self):
        if self.teensy.isOpen():
            self.teensy.close()

if __name__ == "__main__":
    print "Welcome to Example: Autodetect Teensy!"
    try:
        teensy = TeensySerial(115200)
        print "Connected to: %s" % teensy.teensy_port[1]
        teensy.close()
    except TypeError:
        print "Cannot find a Teensy board connected..."
