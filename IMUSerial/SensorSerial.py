from serial import *
from datetime import *
import time

#Setting = 0 means Blink Sensor
#Setting = 1 means IMU
def receiving(usb, setting):
    error = 0;
    usb.timeout = 1
    
    #This hopefully resets the Arduino
    usb.setDTR(False)
    time.sleep(1)
    usb.flushInput()
    usb.setDTR(True)
    
    buffer = ''
    data = []
    while True:
        print buffer
        buffer = usb.readline()
        timeD = datetime.now().time()
        
        if '\n' in buffer:
            lines = buffer.split('\n')
            
            #For the Blink Sensor
            if setting == 0:
                IR1 = lines[-2]
                if '\r' in IR1:
                    IR1Bogus = IR1.split('\r')
                    IR1 = IR1Bogus[0]
                else:
                    IR1 = IR1
                
                try:
                    IR1 = float(IR1)
                except ValueError:
                    error = 1
                    print "Value Error"
                     
                if(error == 1):
                    error = 0
                else:
                    data = [timeD.hour,timeD.minute,timeD.second,timeD.microsecond,IR1]

            #For the IMU
            else:
                last_received_full = lines[-2]

                if '\t' in last_received_full:
                    last_received_tabbed = last_received_full.split('\t')
                    AcclX = float(last_received_tabbed[0])        
                    AcclY = float(last_received_tabbed[1])
                    AcclZ = float(last_received_tabbed[2])
                    MagX = float(last_received_tabbed[3])       
                    MagY = float(last_received_tabbed[4])
                    MagZ = float(last_received_tabbed[5])
                    GyroX = float(last_received_tabbed[6])        
                    GyroY = float(last_received_tabbed[7])
                    GyroZ1 = last_received_tabbed[8]         #Keep this line at the end
                    if '\r' in GyroZ1:
                        GyroZBogus = GyroZ1.split('\r')
                        GyroZ = float(GyroZBogus[0])
                    else:
                        GyroZ = float(GyroZ1)
                    data = [timeD.hour,timeD.minute,timeD.second,timeD.microsecond, AcclX, AcclY, AcclZ, MagX, MagY, MagZ, GyroX, GyroY, GyroZ]
            print data
            return data

if __name__=='__main__':
    usb = Serial('COM3', 57600)
    usb.timeout = 1
    while True:
        receiving(usb,1)
