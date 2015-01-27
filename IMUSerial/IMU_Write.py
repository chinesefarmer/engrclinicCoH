"""
Listen to serial, return most recent numeric values
Lots of help from here:
http://stackoverflow.com/questions/1093598/pyserial-how-to-read-last-line-sent-from-serial-device
"""
import sys
#Ben, change this path to wherever Python is installed. :)
#sys.path.append('/usr/stsci/pyssg/Python-2.7/lib/python2.7/')
from threading import Thread
import time
import serial

last_received = ''

last_received_tabbed = ''
def receiving(ser):
    global last_received
    buffer = ''
    while True:
        buffer = buffer + ser.read(ser.inWaiting())
        #We will only do anything if there are more than 2 lines
        if '\n' in buffer:
            #print buffer
            #This splits the buffer into separate lines based on '\n'
            lines = buffer.split('\n') # Guaranteed to have at least 2 entries
            #The two most recent entries are in lines[-2]
            #last_received = lines[-2]
            last_received_full = lines[-2]
            if '\t' in last_received_full:
                last_received_tabbed = last_received_full.split('\t')
                AcclX = float(last_received_tabbed[0])        #Sensor Interpretation
                AcclY = float(last_received_tabbed[1])
                AcclZ = float(last_received_tabbed[2])
                MagX = float(last_received_tabbed[3])        #Sensor Interpretation
                MagY = float(last_received_tabbed[4])
                MagZ = float(last_received_tabbed[5])
                GyroX = float(last_received_tabbed[6])        #Sensor Interpretation
                GyroY = float(last_received_tabbed[7])
                GyroZ1 = last_received_tabbed[8]         #Keep this line at the end
                if '\r' in GyroZ1:
                    GyroZBogus = GyroZ1.split('\r')
                    GyroZ = float(GyroZBogus[0])
                else:
                    GyroZ = float(GyroZ1)

                print [AcclX, AcclY,  AcclZ, MagX, MagY, MagZ, GyroX, GyroY, GyroZ] 
                return [AcclX, AcclY,  AcclZ, MagX, MagY, MagZ, GyroX, GyroY, GyroZ]               # 
            #If the Arduino sends lots of empty lines, you'll lose the
            #last filled line, so you could make the above statement conditional
            #like so: if lines[-2]: last_received = lines[-2]
            #I think this clears out the buffer to start fresh
            buffer = lines[-1]


class SerialData(object):
    def __init__(self, init=50):
        try:
            #IVAN AND KAT!!! Change the name of the port here to suit your sensor
            #also change the baudrate to what your sensor uses.
            self.ser = ser = serial.Serial(
                port='COM3', #Try to figure out how to automate this!!!
                baudrate=57600,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.1,
                xonxoff=0,
                rtscts=0,
                interCharTimeout=None
            )
        except serial.serialutil.SerialException:
            #no serial connection
            self.ser = None
        else:
            Thread(target=receiving, args=(self.ser,)).start()
        
    def next(self):
        if not self.ser:
            return 100 #return anything so we can test when Arduino isn't connected
        #return a float value or try a few times until we get one
        yay = receiving(self.ser)
        return yay

        
    def __del__(self):
        if self.ser:
            self.ser.close()

if __name__=='__main__':
    s = SerialData()
    for i in range(500):
        time.sleep(.015)
        print s.next()
