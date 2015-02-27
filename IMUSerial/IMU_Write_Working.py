import csv
from serial import *
from math import *
import msvcrt as m
import numpy as np
import pylab as pl

import datetime
import time


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

        #Find the time spent at each angle
        rollDist = timeAtAngle(timeTot,smoothRoll)
        
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
##        pl.plot(timeTot,YawTot)
##        pl.plot(timeTot,smoothYaw)
##        pl.title("Yaw")
        pl.plot(rollDist)
        pl.title("Time spent with head at angle")
        
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

def timeAtAngle(time,angle):
    avgTimeStep = (max(time)-min(time))/len(time)
    print int(max(angle))
    minAngle = int(min(angle))
    # Array of zeros with a fixed size equal to the total number of int angles
    angleTimes = np.zeros(int(max(angle))-minAngle)
    
    print len(angleTimes)
    timeAtAng = []
    for i in range(len(angle)-1):
        angleTimes[int(angle[i])-minAngle - 1] += avgTimeStep
    
    return angleTimes

#Set port and baudRate when calling this function
def receiving(port, baudRate):
    #Initialize variables for roll, pitch, yaw calculations
    roll = 0; pitch = 0; yaw = 0; n = 0; nextR = 0; nextP = 0; nextY = 0; prevR = 0;
    prevP = 0; prevY = 0; gyroDriftX = 0; gyroDriftY = 0; gyroDriftZ = 0
    acclXCal = 0; acclYCal = 0; acclZCal = 0
    
    #Other important variables
    frequencyLoop = 5
    global calibrationNo
    calibrationNo = 100             # Number of iterations during calibration step
    usb = Serial(port, baudRate)
    usb.timeout = 1
    global last_received
    buffer = ''
    error = 0
    # Writes the first line of csv file
    csv_writer(["AcclX","AcclY","AcclZ","MagX","MagY","MagZ","GyroX","GyroY","GyroZ", "Roll", "Pitch", "Yaw", "Time(s)"])
    global startTime
    startTime = time.clock()        # Records Starting time
    
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

                # Will try to save data from buffer to variables.
                # Otherwise will start to the loop over again
                # Prevents indexing errors caused by too few values in the buffer
                try:
                    GyroZ1 = last_received_tabbed[8]         #Keep this line at the end
                except IndexError:
                    continue

                # Makes the string an actual float value
                if '\r' in GyroZ1:
                    GyroZBogus = GyroZ1.split('\r')
                    GyroZ = GyroZBogus[0]
                else:
                    GyroZ = GyroZ1

                # Will try to save data from buffer to variables.
                # Otherwise will start to the loop over again
                # Prevents Value errors caused by non-float buffer values
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
                    continue

                # Calibration Sequence: Accounts for drift of gyro data
                # During calibration, the IMU must be placed on a stationary
                # surface
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
                # Calibration Sequence completed
                else:

                    #Pause initiated to allow users to secure the IMU on user's head
                    global pauseCheck
                    if(pauseCheck == 0):
                        pauseCheck = 1
                        #Should be replaced with GUI interrupt that triggers when
                        #the IMU is secured
                        raw_input("Please put on Headset, then press enter:")
              
                    n = n + 1

                    roll = atan2(AcclZ, AcclY)          # Calculates the roll angle

                    # Calculates the pitch while accounting for edge cases
                    if(AcclZ*sin(roll) + AcclY*cos(roll) == 0):
                        if(AcclX > 0):
                            pitch = pi/2
                        else:
                            pitch = -1*pi/2
                    else:
                        pitch = atan(-1*AcclX / (AcclZ*sin(roll) + AcclY*cos(roll)))

                    yawY = MagZ*sin(roll) - MagY*cos(roll)
                    yawX = MagX*cos(pitch)+ MagY*sin(pitch)*sin(roll) + MagZ*sin(pitch)*cos(roll)
                    yawOffset = 0
                    
                    yaw = atan2(yawY, yawX)
##                    if(yaw
                    
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
                    yaw = abs(nextY*180/pi)
                
                currTime = time.clock() - startTime  # Time elapsed from start
                #Saves the IMU data to a csv file
                data = [AcclX, AcclY, AcclZ, MagX, MagY, MagZ, GyroX, GyroY, GyroZ, roll, pitch, yaw, currTime]
                csv_writer(data)

                # Stops program after a number of samples have been collected
                # Should be replaced with interrupt by GUI
                if(n >= 1000):
                    # Plots the RPY data
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






    
