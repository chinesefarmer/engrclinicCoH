import Spring_BlinkSensor as bs
import Spring_IMUSensor as imu
from serial import *
import csv
from serial import *
from math import *
import msvcrt as m
import numpy as np
import pylab as pl
import time as tm

from datetime import *

if __name__=='__main__':

    global filename,filenameIMU,filenameBlink
    #Writes the raw data for the blink sensor
    filename = raw_input('Enter a file name:  ')+ ".csv"
    #Writes the raw data for the IMU
    filenameIMU = (filename[:-4] + 'IMU.csv' )
    #Reads the data to process for the blink sensor
    filenameBlink = (filename[:-4] + 'Blink.csv' )

    usb = Serial('COM5', 57600)
    blinkSensor = bs.BlinkSensor()
    blinkSensor.CheckKeyPress = False
    blinkSensor.filename = filenameBlink
    bs.initSerialConnection(usb, blinkSensor)
    imuSensor = imu.IMUSensor()
    imuSensor.filenameIMU = filenameIMU
    
    imuSensor.csv_writer(["AcclX","AcclY","AcclZ","MagX","MagY","MagZ","GyroX","GyroY","GyroZ", "Roll", "Pitch", "Yaw", "Time Elapsed(s)"],filenameIMU)
    

    # Settable values for blinkSensor 
    # How often to calculate the number of blinks, in minutes
    blinkSensor.tWindow = 1.0/3
    #How often to print number of blinks in last X minutes, where X is tWindow
    blinkSensor.tPrintBlink = 1.0/6

    '''BEN: This is the loop I'm using right now to keep getting serial data and 
    then save it to a usb when the user hits ctrl-c (or keyboard interrupts the shell)'''

    
    while True:
        try:
            # serialData = [success,[IR, AcclX,AcclY,AcclZ,MagX,MagY,MagZ,GyroX,GyroY,GyroZ]]
            serialData = imuSensor.receiveSerial(usb)

            #Ensures that no errors are in the serialData array
            #serialData[0] == 1 means that there were no failures
            #serialData[0] == 0 means there was at least one failure
            if(serialData[0] == 1):
                #[roll, pitch, self.nextY ,currTime, ready]
                IMUData = imuSensor.calcRPYData(serialData[1])
                # Checks to see if the calibration period has ended
                if(IMUData[4] == 1):
                    # processedData = [smoothRoll,smoothPitch,smoothYaw,
                    # self.timeAtRoll,self.timeAtPitch,self.timeAtYaw, # THESE ARE 360 length array
                    # rollMax,rollFocus, pitchMax ,pitchFocus, yawMax ,yawFocus] # *Max is the focus angle and
                                                                        # *focus is the percent time focusing
                    processedData = imuSensor.processIMUData(IMUData)

                    # Handles the IR Sensor
                    try:
                       IR1 = float((serialData[1])[0])
                       numRecentBlinks = blinkSensor.Algorithm(IR1, False)
                       if(numRecentBlinks != 0):
                            print numRecentBlinks

                    except ValueError:
                       print "Value Error"

                    # Slows down the cycle enough to prevent divide by zero errors
                    tm.sleep(.001)

                    
##      Run only at the end of the op  
        except KeyboardInterrupt:  

            # Don't need to includ this. Ben's testing
            imuSensor.plotter()
            
            usb.close()
            blinkSensor.saveFile()

            # Remove for the real code
            blinkSensor.csv_reader(1)
            break
