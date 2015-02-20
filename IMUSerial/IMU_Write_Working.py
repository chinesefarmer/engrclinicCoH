import csv
from serial import *
from math import *
import msvcrt as m
import numpy as np
import pylab as pl

import datetime
import time

from IMU_filter import activeFilter


pauseCheck = 0;                                 # Debug code

#The function writes a comma-delimited row of data into the file "filename"
#When opening the csv file, remember to select the delimiter as commas
#(open office is stupid and won't put the data in separate columns otherwise)
def csv_writer(data):
    with open(filename, 'a') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        writer.writerow(data)
#Reads the comma-delimited csv file and writes it to lists.
#Then plots the lists.
def csv_reader():
    with open(filename, 'r') as csv_file:
        reader = csv.reader(csv_file, delimiter = ',')

        RollTot = [];
        PitchTot = [];
        YawTot = [];
        timeTot = [];

        # Skips the first line which does not contain data
        next(reader)
        # Skips the calibration sequence to arrive at relevant
        # RPY data
        for i in range(calibrationNo):
            next(reader)
        #Creates a list for RPY and time from the
            #csv file
        for row in reader:
            RollTot.append(float(row[9]))
            PitchTot.append(float(row[10]))
            YawTot.append(float(row[11]))
            timeTot.append(float(row[12]))
            
        #Applies the moving average
        smoothRoll = avgFilter(RollTot)
        smoothPitch = avgFilter(PitchTot)
        smoothYaw = avgFilter(YawTot)
        
        #Plots the RPY data in a 3x1 figure with titles
        pl.figure(1)
        pl.subplot(311)
        pl.plot(timeTot,RollTot)
        pl.plot(timeTot,smoothRoll)
        pl.title("Roll")
        pl.subplot(312)
        pl.plot(timeTot,PitchTot)
        pl.plot(timeTot,smoothPitch)
        pl.title("Pitch")
        pl.subplot(313)
        pl.plot(timeTot,YawTot)
        pl.plot(timeTot,smoothYaw)
        pl.title("Yaw")
        pl.show()
        
#Applies a moving average filter
def avgFilter(imuSignal):
    avgSize = 10            #Determines the size of the avg filter
    sigSize = len(imuSignal)
    #Applies moving average
    smoothSig = np.convolve(imuSignal, np.ones(avgSize)/avgSize, mode='same')
    #Sets the first and last few smoothed values to
    for i in range(avgSize):
        smoothSig[i]=smoothSig[avgSize]
        smoothSig[sigSize - 1 - i] = smoothSig[sigSize - 1 - avgSize]
    return smoothSig

#Set port and baudRate when calling this function
def receiving(port, baudRate):
    #Initialize variables for roll, pitch, yaw calculations
    roll = 0; pitch = 0; yaw = 0; n = 0; nextR = 0; nextP = 0; nextY = 0; prevR = 0;
    prevP = 0; prevY = 0; gyroDriftX = 0; gyroDriftY = 0; gyroDriftZ = 0
    acclXCal = 0; acclYCal = 0; acclZCal = 0
    
    #Other important variables
    frequencyLoop = 5
    global calibrationNo
    calibrationNo = 100
    usb = Serial(port, baudRate)
    usb.timeout = 1
    global last_received
    buffer = ''
    error = 0
    csv_writer(["AcclX","AcclY","AcclZ","MagX","MagY","MagZ","GyroX","GyroY","GyroZ", "Roll", "Pitch", "Yaw", "Time(s)"])
    global startTime
    startTime = time.clock()
    
    while True:

        #It also works if you just read the line instead of using a legit buffer
        buffer = usb.readline()
        #buffer = buffer + usb.read(usb.inWaiting())
        #raw_input("Press enter to continue...")
            
        if '\n' in buffer:
            lines = buffer.split('\n')
            last_received_full = lines[-2]

            if '\t' in last_received_full:
                last_received_tabbed = last_received_full.split('\t')
##                print(last_received_tabbed)
##                print len(last_received_tabbed)

                try:
                    GyroZ1 = last_received_tabbed[8]         #Keep this line at the end
                except IndexError:
##                    print "INDEX ERROR XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
                    continue
                
                if '\r' in GyroZ1:
                    GyroZBogus = GyroZ1.split('\r')
                    GyroZ = GyroZBogus[0]
                else:
                    GyroZ = GyroZ1
                try:
                    AcclX = float(last_received_tabbed[0])        
                    AcclY = float(last_received_tabbed[1])
                    AcclZ = float(last_received_tabbed[2])
                    MagX = float(last_received_tabbed[3])       
                    MagY = float(last_received_tabbed[4])
                    MagZ = float(last_received_tabbed[5])
                    GyroX = float(last_received_tabbed[6])        
                    GyroY = float(last_received_tabbed[7])
                    GyroZ = float(GyroZ)
                except ValueError:
##                    print "VALUE ERROR OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO"
                    continue
                global pauseCheck
                if(pauseCheck == 0):
                    acclXCal += AcclX
                    acclYCal += AcclY
                    acclZCal += AcclZ
                    
                
                if (n < 5):
                    n = n + 1
                elif(n < calibrationNo - 1):
                    n = n + 1
                    gyroDriftX = gyroDriftX + -1*GyroX
                    gyroDriftY = gyroDriftY + -1*GyroY
                    gyroDriftZ = gyroDriftZ + -1*GyroZ

                elif(n == calibrationNo - 1):
                    n = n + 1
                    gyroDriftX = gyroDriftX + calibrationNo
                    gyroDriftY = gyroDriftY + calibrationNo
                    gyroDriftZ = gyroDriftZ + calibrationNo

                else:
    
                    if(pauseCheck == 0):                                            #Debugging
                        pauseCheck = 1
                        acclXCal /= calibrationNo
                        acclYCal /= calibrationNo
                        acclZCal /= calibrationNo
                        print acclXCal
                        print acclYCal
                        print acclZCal
                        acclMagn = sqrt(acclXCal*acclXCal +acclYCal*acclYCal +acclZCal*acclZCal)
                        print "acclMagnitude"
                        print acclMagn

                        w = -(acos(acclXCal/acclMagn)-pi/2)
                        p = -(acos(acclYCal/acclMagn)-pi/2)
                        k = -acos(acclZCal/acclMagn)
                        print "Angles"
                        print (w*180/pi)             #from x
                        print (p*180/pi)
                        print (k*180/pi)

                        rotX1 = cos(p)*cos(k)                   #Calculate rotation matrix constants
                        rotX2 = cos(w)*sin(k)+sin(w)*sin(p)*cos(k)
                        rotX3 = sin(w)*sin(k) - cos(w)*sin(p)*cos(k)

                        rotY1 = -cos(p)*sin(k)
                        rotY2 = cos(w)*cos(k) - sin(w)*sin(p)*sin(k)
                        rotY3 = sin(w)*cos(k)+cos(w)*sin(p)*sin(k)

                        rotZ1 = sin(p)
                        rotZ2 = -sin(w)*cos(p)
                        rotZ3 = cos(w)*cos(p)
##                        print xAngleOffset
##                        print yAngleOffset
##                        print zAngleOffset
                        
                        

                        AcclX = acclXCal
                        AcclY = acclYCal
                        AcclZ = acclZCal
                        
                        coordAcclX = rotX1*AcclX + rotX2*AcclY + rotX3*AcclZ
                        coordAcclY = rotY1*AcclX + rotY2*AcclY + rotY3*AcclZ
                        coordAcclZ = rotZ1*AcclX + rotZ2*AcclY + rotZ3*AcclZ
                        print "Rotated Vector"
                        print coordAcclX
                        print coordAcclY
                        print coordAcclZ
                        
                        raw_input("Please put on Headset, then press enter:")        #Debugging
##                        
##                        
##                    coordAcclX = rotX1*AcclX + rotX2*AcclY + rotX3*AcclZ
##                    coordAcclY = rotY1*AcclX + rotY2*AcclY + rotY3*AcclZ
##                    coordAcclZ = rotZ1*AcclX + rotZ2*AcclY + rotZ3*AcclZ
##
##                    AcclX = coordAcclX
##                    AcclY = coordAcclY
##                    AcclZ = coordAcclZ
##
##                    
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

                currTime = time.clock() - startTime
                data = [AcclX, AcclY, AcclZ, MagX, MagY, MagZ, GyroX, GyroY, GyroZ, roll, pitch, yaw, currTime]
                data = activeFilter(data)
                csv_writer(data)

                if(n >= 1000):
                    csv_reader()
                    break



##                AcclXTot.append(AcclX);
##                if(n == 200):
##                    print len(AcclXTot)
##                    numSamples = np.linspace(1,200,200)
##                    print len(numSamples)
##                    print AcclXTot
##                    print numSamples
##                
##                    pl.plot(numSamples, AcclX)
##                    pl.show()

##                print "-----------------------------------------" 
##                print "Accl \t\t Mag \t\t Gyro"
##                print "X: " + str(AcclX) + "  \tX: " + str(MagX) + "\tX: " + str(GyroX)
##                print "Y: " + str(AcclY) + "  \tY: " + str(MagY) + "  \tY: " + str(GyroY)
##                print "Z: " + str(AcclZ) + "  \tZ: " + str(MagZ) + "  \tZ: " + str(GyroZ) + "\n"
##                print "Roll: " + str(roll) + "  \tPitch: " + str(pitch) + "  \tYaw: " + str(yaw)
##                print "Sample Number is: " + str(n)
##                print "-----------------------------------------"
##                print " "



            #buffer = lines[-1]
                

if __name__=='__main__':
    filename = raw_input('Enter a file name:  ')+ ".csv"
    arduinoData = receiving('COM3',57600)






    
