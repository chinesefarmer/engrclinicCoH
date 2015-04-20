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

    usb = Serial('COM6', 57600)
    blinkSensor = bs.BlinkSensor()
    blinkSensor.CheckKeyPress = False
    blinkSensor.filename = filenameBlink
    bs.initSerialConnection(usb, blinkSensor)
    imuSensor = imu.IMUSensor()
    imuSensor.filenameIMU = filenameIMU
    
    imuSensor.csv_writer(["AcclX","AcclY","AcclZ","MagX","MagY","MagZ","GyroX","GyroY","GyroZ", "Roll", "Pitch", "Yaw", "Time Elapsed(s)"],filenameIMU)
    
    '''BEN: This is the loop I'm using right now to keep getting serial data and 
    then save it to a usb when the user hits ctrl-c (or keyboard interrupts the shell)'''
    while True:
        try:
            serialData = imuSensor.receiveSerial(usb)

            #Ensures that no errors are in the serialData array
            #serialData[0] == 1 means that there were no failures
            #serialData[0] == 0 means there was at least one failure
            if(serialData[0] == 1):
                #[roll, pitch, yaw, currTime]
                IMUData = imuSensor.calcRPYData(serialData[1])
                # Checks to see if the calibration period has ended
                if(IMUData[4] == 1):
                    processedData = imuSensor.processIMUData(IMUData)

                    try:
                       IR1 = float((serialData[1])[0])
                       blinkSensor.Algorithm(IR1, False)
                    except ValueError:
                       print "Value Error"

                    # Slows down the cycle enough to prevent divide by zero errors
                    tm.sleep(.001)

        except KeyboardInterrupt:  
            imuSensor.plotter()
            usb.close()
            blinkSensor.saveFile()
            # Remove for the real code
            blinkSensor.csv_reader(1)
            usb.close()
            break
