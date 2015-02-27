import csv
from math import *
from SensorSerial import *
import msvcrt as m
import numpy as np
import pylab as pl

from IMU_filter import activeFilter


pauseCheck = 0;                                 # Debug code


#When opening the csv file, remember to select the delimiter as commas
#(open office is stupid and won't put the data in separate columns otherwise)
def csv_writer(data):
    with open(filename, 'a') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        writer.writerow(data)

#Set port and baudRate when calling this function
def process(port, baudRate):
    #Initialize variables for roll, pitch, yaw calculations
    roll = 0; pitch = 0; yaw = 0; n = 0; nextR = 0; nextP = 0; nextY = 0; prevR = 0;
    prevP = 0; prevY = 0; gyroDriftX = 0; gyroDriftY = 0; gyroDriftZ = 0
    AcclXTot = np.array([]);
    AcclYTot = [];
    AcclZTot = [];

    GyroXTot = [];
    GyroYTot = [];
    GyroZTot = [];

    MagXTot = [];
    MagYTot = [];
    MagZTot = [];

    RollTot = [];
    PitchTot = [];
    YawTot = [];
    
    #Other important variables
    frequencyLoop = 5
    calibrationNo = 100
    
    usb = Serial(port, baudRate)
    usb.timeout = 1


    csv_writer(["Hour","Minute","Second","MicroSec","AcclX","AcclY","AcclZ","MagX","MagY","MagZ","GyroX","GyroY","GyroZ", "Roll", "Pitch", "Yaw"])
    
    while True:
        data = receiving(usb,1)
        print data
        AcclX = data[4]; AcclY = data[5]; AcclZ = data[6]; MagX = data[7]; MagY = data[8]; MagZ = data[9];
        GyroX = data[10]; GyroY = data[11]; GyroZ = data[12]; Hour = data[0]; Minute = data[1]; Second = data[2];
        MicroSec = data[3]
        

        if (n < 5):
            n = n + 1
        elif(n < calibrationNo):
            n = n + 1
            gyroDriftX = gyroDriftX + -1*GyroX
            gyroDriftY = gyroDriftY + -1*GyroY
            gyroDriftZ = gyroDriftZ + -1*GyroZ
        elif(n == calibrationNo):
            n = n + 1
            gyroDriftX = gyroDriftX + calibrationNo
            gyroDriftY = gyroDriftY + calibrationNo
            gyroDriftZ = gyroDriftZ + calibrationNo
        else:
            
            global pauseCheck
            if(pauseCheck == 0):                                            #Debugging
##                        x = [1, 2, 3, 4, 5]
##
##                        y = [1, 4, 9, 16, 25]
##
##                        pl.plot(x, y)
##                        pl.show()
                pauseCheck = 1
                raw_input("Please put on Headset, then press enter:")        #Debugging

            
            n = n + 1
            roll = atan2(AcclY, AcclZ)
            if(AcclY*sin(roll) + AcclZ*cos(roll) == 0):
                if(AcclX > 0):
                    pitch = pi/2
                else:
                    pitch = -1*pi/2
            else:
                pitch = atan(-1*AcclX / (AcclY*sin(roll) + AcclZ*cos(roll)))
            yaw = atan2(MagZ*sin(roll) - MagY*cos(roll), MagX*cos(pitch)+
                        MagY*sin(pitch)*sin(roll) + MagZ*sin(pitch)*cos(roll))

            gX = abs(GyroX + gyroDriftX)
            gY = abs(GyroY + gyroDriftY)
            gZ = abs(GyroZ + gyroDriftZ)

            prevR = nextR
            prevP = nextP
            prevY = nextY

            nextR = (prevR + roll*gX) / (1 + gX)
            nextP = (prevP + pitch * gY) / (1 + gY)
            nextY = (prevY + yaw * gZ) / (1 + gZ)

            roll = nextR*180/pi
            pitch = -1*nextP*180/pi
            yaw = nextY*180/pi
                    
            fullData = [Hour, Minute, Second, MicroSec, AcclX, AcclY, AcclZ, MagX, MagY, MagZ, GyroX, GyroY, GyroZ, roll, pitch, yaw]
            fullData = activeFilter(fullData)
            csv_writer(fullData)

            AcclXTot.append(AcclX);
            if(n == 200):
                print len(AcclXTot)
                numSamples = np.linspace(1,200,200)
                print len(numSamples)
                print AcclXTot
                print numSamples
            
                pl.plot(numSamples, AcclX)
                pl.show()

                

if __name__=='__main__':
    filename = raw_input('Enter a file name:  ')+ ".csv"
    arduinoData = process('COM3',57600)






    
