################################################################################
# This piece of code is developed by the 2014-2015 City of Hope-Tracking team 
# from Harvey Mudd College
# This file provides a class and member functions that can receive the serial 
# communication from the teensy 3.1 that contains all the IMU and blink sensor 
# collected. It can process the IMU data collected through filtering, calculate 
# the roll, pitch and yaw angles of rotation (RPY) from the collected IMU data calculating
# sample distribution of each of the angles (the number of samples that correspond
# to each RPY angle), and will calculate the percentage of time the user has been
# focusing on the target operating point.
# 
# As of hardware, the sensor package is required to run the program properly. 
# specifically, the arduino teensy 3.1 needs to be connected to one of the COM ports
# on the computer.

# Additional arduino, python libraries also need to be installed. 
# Please see the installation section in the appendix of the final report for details.
# Code was last changed at:
# May 6, 2015, Claremont, California 
################################################################################

# The data saved is only the unfiltered RPY and IMU and blink sensing data received
# by the teensy

import csv
from serial import *
from math import *
import msvcrt as m
import numpy as np
import pylab as pl
import time as tm 
from datetime import *

#----------Global Variables for the IMU--------------------------------

#---------------------------------------------------------------------
class IMUSensor:
    def __init__(self):
        # Customizable Parameters --------------------------------------------

        self.avgWeightingRoll = .2         # These are the weighting values 
        self.avgWeightingPitch = .2        # that apply smoothing on the roll, 
        self.avgWeightingYaw = .5          # pitch and yaw

        # Max Possible Pitch angle and still be facing the table
        self.ACCEPTABLE_ROLL_RANGE = 5  
        self.ACCEPTABLE_PITCH_RANGE = 10     
        self.ACCEPTABLE_YAW_RANGE = 8

        # Number of iterations during calibration step
        self.calibrationNo = 100

        # The weighting factor that prevents the error from the yaw angle
        # calculation from accumulating
        self.gyroReFocus = .9995
        # -----------------------------------------------------------------------
        # Parameters required for operation (Non-Customizable)------------------- 

        # Required for some functions
        self.trialNum = 0;          # Number of data points captured
        self.nextR = 0;             # Stores one RPY value for later processing
        self.nextP = 0; 
        self.nextY = 0; 
        self.gyroDriftX = 0;        # Constant used to counterbalance gyro drift
        self.gyroDriftY = 0; 
        self.gyroDriftZ = 0

        self.pauseCheck = 0                 # A parameter that denotes when the
                                            # the system is done with calibration

        # Records the start time
        timeStamp = datetime.now().time()
        self.startTime = ((timeStamp.hour*60 + timeStamp.minute + 
                    (timeStamp.second + 
                    0.000001*timeStamp.microsecond)/60))*60

        # Stores one previous RPY value for processing
        self.previousR = 0;
        self.previousP = 0;
        self.previousY = 0;

        # Time of the previous sample
        self.previousTime = 0;

        # Makes an array of 360 zeroes which will be populated by the number of samples
        # at each angle
        self.timeAtRoll = np.zeros(360)
        self.timeAtPitch = np.zeros(360)
        self.timeAtYaw = np.zeros(360)

        # The name of the file that will have all the sensor data saved to it
        self.filenameIMU = ''
# -------------------------------------------------------------------------------
# Member functions ------------------------------------------------------------
    
    # Description: Writes the comma-delimited csv file that saves all of the IMU data
    def csv_writer(self, data,nameOfFile):
        with open(nameOfFile, 'a') as csv_file:
            writer = csv.writer(csv_file, delimiter=',')
            writer.writerow(data)

    # Description: This function will read the serial port communication data written by
    # the teensy 3.1 and will receive both IMU data and the Blink sensor data.
    # Note: Will return 0 if the function fails to receive readable data from serial and
    # will return 1 if the function succeeds
    def receiveSerial(self,usb):

        serialData = []
        #It also works if you just read the line instead of using a legit buffer
        buffer = usb.readline()
        
        # Conditions the serial comm data so that it is readable by Python and cause the 
        # program to skip corrupted incoming serial data from processing
        if '\n' in buffer:
            lines = buffer.split('\n')
            last_received_full = lines[-2]

            if '\t' in last_received_full:
                last_received_tabbed = last_received_full.split('\t')

                # Will try to save data from buffer to variables.
                # Otherwise will start to the loop over again
                # Prevents indexing errors caused by too few values in the buffer
                try:
                    GyroZ1 = last_received_tabbed[9]         #Keep this line at the end
                except IndexError:
                    return [0, serialData]

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
                    IR = float(last_received_tabbed[0])
                    AcclX = float(last_received_tabbed[1])        
                    AcclY = float(last_received_tabbed[2])
                    AcclZ = float(last_received_tabbed[3])
                    MagX = float(last_received_tabbed[4])       
                    MagY = float(last_received_tabbed[5])
                    MagZ = float(last_received_tabbed[6])
                    GyroX = float(last_received_tabbed[7])        
                    GyroY = float(last_received_tabbed[8])
                    GyroZ = float(GyroZ)
                    serialData = [IR, AcclX,AcclY,AcclZ,MagX,MagY,MagZ,GyroX,GyroY,GyroZ]
                    return [1, serialData]
                except ValueError:
                    return [0, serialData]
        return [0, serialData]

    # Description: Calculates the roll, pitch and yaw angles of rotation and saves the data to 
    # file. Will initiate a calibration sequence during the first self.calibrationNo number of
    # times that this function has been called. This will produce a constant that attempts to
    # minimize the drift caused by gyroscope noise that is integrated to get the yaw angle of
    # rotation
    def calcRPYData(self,serialData):
        [IR1,AcclX,AcclY,AcclZ,MagX,MagY,MagZ,GyroX,GyroY,GyroZ] = serialData
        #Initialize variables for requried roll, pitch, yaw calculations

        # 0 means that the calibration sequence has not been completed
        # 1 means that the calibration sequence has been completed
        ready = 0

        # Initializes the roll and pitch
        roll = 0
        pitch = 0

        #Time elapsed from start
        timeStamp = datetime.now().time()
        currTime = ((timeStamp.hour*60 + timeStamp.minute + (timeStamp.second + 0.000001*timeStamp.microsecond)/60))*60 - self.startTime
        # Calibration Sequence: Accounts for drift of gyro data
        # During calibration, the IMU must be placed on a stationary
        # surface
        if (self.trialNum < 5):
            self.trialNum = self.trialNum + 1

        elif(self.trialNum < self.calibrationNo - 1):
            self.trialNum = self.trialNum + 1
            self.gyroDriftX = self.gyroDriftX - GyroX
            self.gyroDriftY = self.gyroDriftY - GyroY
            self.gyroDriftZ = self.gyroDriftZ - GyroZ
        elif(self.trialNum == self.calibrationNo - 1):
            self.trialNum = self.trialNum + 1
            self.gyroDriftX = self.gyroDriftX / self.calibrationNo
            self.gyroDriftY = self.gyroDriftY / self.calibrationNo
            self.gyroDriftZ = self.gyroDriftZ / self.calibrationNo

        # Calibration Sequence completed
        else:

            ready = 1
            
            #Time elapsed from start
            timeStamp = datetime.now().time()
            currTime = ((timeStamp.hour*60 + timeStamp.minute + (timeStamp.second + 0.000001*timeStamp.microsecond)/60))*60 - self.startTime


            #Pause initiated to allow users to secure the IMU on user's head
            if(self.pauseCheck == 0):
                self.pauseCheck = 1
                #Should be replaced with GUI interrupt that triggers when
                #the IMU is secured
                timeStamp = datetime.now().time()
                currTime = ((timeStamp.hour*60 + timeStamp.minute + (timeStamp.second + 0.000001*timeStamp.microsecond)/60))*60 - self.startTime

                self.previousTime = currTime

                print "IMU Calibration Sequence Completed: Please place the IMU on your head"
            
            self.trialNum = self.trialNum + 1


            roll = atan2(AcclZ, AcclY)          # Calculates the roll angle
            pitch = 0
            # Calculates the pitch while accounting for edge cases
            if(AcclZ*sin(roll) + AcclY*cos(roll) == 0):
                if(AcclX > 0):
                    pitch = pi/2
                else:
                    pitch = -1*pi/2
            else:
                pitch = atan(-1*AcclX / (AcclZ*sin(roll) + AcclY*cos(roll)))
            
            # These are weightings used for filters, which are always positive
            gX = abs(GyroX + self.gyroDriftX)
            gY = GyroY + self.gyroDriftY
            gZ = abs(GyroZ + self.gyroDriftZ)

            # Sets the prev variable to the rpy data set in the previous loop
            prevR = self.nextR
            prevP = self.nextP
            prevY = self.nextY

            # Minimizes the error of roll and pitch by checking the calculated valley
            # with the gyroscope.
            self.nextR = (prevR + roll*gX) / (1 + gX)
            self.nextP = (prevP + pitch * gZ) / (1 + gZ)

            roll = self.nextR*180/pi
            pitch = -1*self.nextP*180/pi

            # Makes Roll and Pitch range betweem -180 to 180 degrees
            if(roll>180):
                roll = roll - 360
            elif(roll<-180):
                roll = roll + 360

            if(pitch>180):
                pitch = pitch - 360
            elif(pitch<-180):
                pitch = pitch + 360

            # Calculates the yaw from the y-axis gyroscope
            self.nextY = self.calcGyroYaw(prevY,currTime,gY)
        
        #Saves the IMU data to a csv file
        data = [AcclX, AcclY, AcclZ, MagX, MagY, MagZ, GyroX, GyroY, GyroZ, roll, pitch, self.nextY, currTime]
        self.csv_writer(data,self.filenameIMU)
        return [roll, pitch, self.nextY ,currTime, ready]

    # Description: Calculates the yaw from the y-axis gyroscope and weights the value
    # to remove the accumulated error from the gyroscope noise. The weight also will 
    # cause the sensor to refocus the 0 value to be wherever the sensor has been facing
    # for a long period of time. Refocus happens when a certain orientaion corresponding
    # to a non-zero yaw value is focused on for too long and the yaw is decreased to zero.
    def calcGyroYaw(self,previousY, currTime, gyroY):
        # The yaw calculation
        yawAngle = ((gyroY*(currTime-self.previousTime)+previousY)*self.gyroReFocus)

        # Makes yaw range betweem -180 to 180 degrees
        if(yawAngle > 180):
            yawAngle = 180
        elif(yawAngle <-180):
            yawAngle = -180
        return yawAngle


    # Description: Processes the IMU data by filtering it, finding the time distribution of
    # each of the angles, and then calculating the percentage that the user is focusing on
    # the target operating field.
    def processIMUData(self,IMUData):
        
        [roll, pitch, yaw, currTime, ready] = IMUData

        # Filters the roll, pitch, and yaw
        smoothRoll = self.rtSmoothFilter(self.previousR, roll, self.avgWeightingRoll);
        smoothPitch = self.rtSmoothFilter(self.previousP, pitch, self.avgWeightingPitch);
        smoothYaw = self.rtSmoothFilter(self.previousY,yaw,self.avgWeightingYaw)

        # Calculates the time that the IMU is oriented at each of the angles in
        #  roll, pitch, and yaw
        self.timeAtAngle(smoothRoll,smoothPitch,smoothYaw)

        # Calculates the percentage focus
        # The integer values 0, 1, and 2 denote which RPY data is being passed
        # roll = 0
        # pitch = 1
        # yaw = 2
        [rollMax ,rollFocus] = self.percentFocus(self.timeAtRoll,0)
        [pitchMax ,pitchFocus] = self.percentFocus(self.timeAtPitch,1)
        [yawMax ,yawFocus] = self.percentFocus(self.timeAtYaw,2)

        # Saves previous values
        self.previousR = smoothRoll
        self.previousP = smoothPitch
        previousY = smoothYaw
        self.previousTime = currTime

        return [smoothRoll,smoothPitch,smoothYaw, self.timeAtRoll,self.timeAtPitch,self.timeAtYaw, rollMax ,rollFocus, pitchMax ,pitchFocus, yawMax ,yawFocus]

    # Description: Applies a real time exponential moving average filter
    def rtSmoothFilter(self,prevRPY,rpyData, avgWeighting):
        smoothedData = rpyData*avgWeighting + (1-avgWeighting)*prevRPY
        return smoothedData

    # Description: Updates an array with 360 elements where each index corresponds
    # to an angle and the value at the index corresponds to the number of samples
    # that has occured at that angle
    def timeAtAngle(self,roll,pitch,yaw):
        
        # Corrects for the fact that RPY range is between 180 and -180
        # Note: There may be some off by one errors that appear very rarely
        roll += 180
        pitch += 180
        yaw += 179

        # Increments the array at the correct index(or angle)
        self.timeAtRoll[int(roll)] += 1
        self.timeAtPitch[int(pitch)] += 1
        self.timeAtYaw[int(yaw)] += 1

    # Description: 
    # Calculates the approximate orientation that the head needs to be oriented in 
    # order to be facing the operating field and calculates the percentage of time 
    # the head is facing that way (for the pitch orientation)
    # The percentage focus is calculated out of the total time and is not windowed.
    # For future additions, a similar function as this that incorporates windowing
    # may be useful

    # Finds operating angle by finding  the angle that takes the max time
    # The roll reading will does not calculate if the user is focusing on the operating field
    # but the angle at which the head tilted for the longest time and what percentage of the
    # total time the head has been tilted there + or - a range.
    def percentFocus(self,angles,RPYtype):

        # acceptableRange is the range about a central angle that is allowed to count as
        # still facing the operating table
        # 5 is a dummy value that will be overwritten
        acceptableRange = 5

        # Sets the acceptable range
        # Roll
        if(RPYtype == 0):
            acceptableRange = self.ACCEPTABLE_ROLL_RANGE
        # Pitch
        elif(RPYtype == 1):
            acceptableRange = self.ACCEPTABLE_PITCH_RANGE
        # Yaw
        elif(RPYtype == 2):
            acceptableRange = self.ACCEPTABLE_YAW_RANGE

        timeTarget = 0
        totSamples = self.trialNum - self.calibrationNo

        # Calculates the angle that currently has experienced the most samples
        operateAngle = np.argmax(angles)
        timeTarget = 0              # Time facing the target operating field
        for i in range(2*acceptableRange):
            iterAngle = operateAngle + i - acceptableRange

            # Need to rewrite so that it wraps around
            # Currently if it is out of range, the samples at the angles are 
            # not counted
            if(iterAngle < 0 or iterAngle > 360):
                continue
            else:
                timeTarget += angles[iterAngle]

        return [operateAngle, timeTarget/(self.trialNum-self.calibrationNo)]


    # Description: A Debugging function that allows the programmer to view
    # basic plots to help assess if the function is working correctly
    def plotter(self):
        pl.figure(1)
        pl.subplot(411)
        pl.plot(self.timeAtRoll)
        pl.subplot(412)
        pl.plot(self.timeAtPitch)
        pl.subplot(413)
        pl.plot(self.timeAtYaw)
        pl.show()
