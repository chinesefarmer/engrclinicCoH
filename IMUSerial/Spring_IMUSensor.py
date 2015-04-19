import csv
from serial import *
from math import *
import msvcrt as m
import numpy as np
import pylab as pl
import time as tm

#import datetime
#import time

from datetime import *

#----------Global Variables for the IMU--------------------------------

#---------------------------------------------------------------------
class IMUSensor:
    def __init__(self):
        # Customizable Parameters
        self.avgWeightingRoll = 0.5
        self.avgWeightingPitch = 0.5
        self.avgWeightingYaw = 0.5
        self.pauseCheck = 0                                 # Debug code
        # Max Possible Pitch angle and still be facing the table
        self.ACCEPTABLE_ROLL_RANGE = 5   
        self.ACCEPTABLE_PITCH_RANGE = 5      
        self.ACCEPTABLE_YAW_RANGE = 3

        self.calibrationNo = 100             # Number of iterations during calibration step

        # Required for some functions
        self.trialNum = 0;
        self.nextR = 0; 
        self.nextP = 0; 
        self.nextY = 0; 
        self.gyroDriftX = 0; 
        self.gyroDriftY = 0; 
        self.gyroDriftZ = 0

        timeStamp = datetime.now().time()
        self.startTime = ((timeStamp.hour*60 + timeStamp.minute + 
                    (timeStamp.second + 
                    0.000001*timeStamp.microsecond)/60))*60

        self.previousR = 0;
        self.previousP = 0;
        self.previousY = 0;
        self.previousTime = 0;

        # Makes an array of 360 zeroes which will be populated by the number of samples
        # at each angle
        self.timeAtRoll = np.zeros(360)
        self.timeAtPitch = np.zeros(360)
        self.timeAtYaw = np.zeros(360)

        #For Testing
        self.smoothYawAll = []

        self.filenameIMU = ''
    def csv_writer(self, data,nameOfFile):
        with open(nameOfFile, 'a') as csv_file:
            writer = csv.writer(csv_file, delimiter=',')
            writer.writerow(data)

    # Will return 0 if the function fails to receive readable data from serial and
    # will return 1 if the function succeeds
    def receiveSerial(self,usb):

        serialData = []
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


    def calcRPYData(self,serialData):
        [IR1,AcclX,AcclY,AcclZ,MagX,MagY,MagZ,GyroX,GyroY,GyroZ] = serialData
        #Initialize variables for requried roll, pitch, yaw calculations

        # 0 means that the calibration sequence has not been completed
        # 1 means that the calibration sequence has been completed
        ready = 0
        roll = 0
        pitch = 0

        timeStamp = datetime.now().time()
        #Time elapsed from start
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
            timeStamp = datetime.now().time()
            #Time elapsed from start
            currTime = ((timeStamp.hour*60 + timeStamp.minute + (timeStamp.second + 0.000001*timeStamp.microsecond)/60))*60 - self.startTime


            #Pause initiated to allow users to secure the IMU on user's head
            if(self.pauseCheck == 0):
                self.pauseCheck = 1
                #Should be replaced with GUI interrupt that triggers when
                #the IMU is secured
                raw_input("Please put on Headset, then press enter:")
                timeStamp = datetime.now().time()
                currTime = ((timeStamp.hour*60 + timeStamp.minute + (timeStamp.second + 0.000001*timeStamp.microsecond)/60))*60 - self.startTime

                self.previousTime = currTime
            
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
            
            gX = abs(GyroX + self.gyroDriftX)
            gY = abs(GyroY + self.gyroDriftY)
            gZ = abs(GyroZ + self.gyroDriftZ)

            # Sets the prev variable to the rpy data set in the previous loop
            prevR = self.nextR
            prevP = self.nextP
            prevY = self.nextY

            self.nextR = (prevR + roll*gX) / (1 + gX)
            self.nextP = (prevP + pitch * gZ) / (1 + gZ)

            roll = self.nextR*180/pi
            pitch = -1*self.nextP*180/pi

            # Makes Roll, Pitch, and Yaw range betweem -180 to 180 degrees
            if(roll>180):
                roll = roll - 360
            elif(roll<-180):
                roll = roll + 360

            if(pitch>180):
                pitch = pitch - 360
            elif(pitch<-180):
                pitch = pitch + 360


            self.nextY = self.calcGyroYaw(prevY,currTime,GyroY)
        
        #Saves the IMU data to a csv file
        data = [AcclX, AcclY, AcclZ, MagX, MagY, MagZ, GyroX, GyroY, GyroZ, roll, pitch, self.nextY, currTime]
        self.csv_writer(data,self.filenameIMU)
        return [roll, pitch, self.nextY ,currTime, ready]


    def calcGyroYaw(self,previousY, currTime, gyroY):
        yawAngle = ((gyroY*(currTime-self.previousTime)+previousY)*.9)

        # yawAngle = (((gyroY+self.gyroDriftY)*(currTime-self.previousTime)+previousY)*.998)

        # CHECK THIS LATER
        if(yawAngle > 180):
            yawAngle = 180
        elif(yawAngle <-180):
            yawAngle = -180
        return yawAngle



    def processIMUData(self,IMUData):
        
        [roll, pitch, yaw, currTime, ready] = IMUData
        smoothRoll = self.rtSmoothFilter(self.previousR, roll, self.avgWeightingRoll);
        smoothPitch = self.rtSmoothFilter(self.previousP, pitch, self.avgWeightingPitch);
        smoothYaw = self.rtSmoothFilter(self.previousY,yaw,self.avgWeightingYaw)

        self.timeAtAngle(smoothRoll,smoothPitch,smoothYaw)


        # The integer values denote which RPY data is being passed
        [rollMax ,rollFocus] = self.percentFocus(self.timeAtRoll,0)
        # Because it is pitch, the percent focus algorithm bounds the information
        # to angles that correspond to looking downwards towards the operating table
        [pitchMax ,pitchFocus] = self.percentFocus(self.timeAtPitch,1)
        [yawMax ,yawFocus] = self.percentFocus(self.timeAtYaw,2)

        print "------------------------------"
        print rollMax
        print rollFocus
        print pitchMax
        print pitchFocus
        print yawMax
        print yawFocus

        self.previousR = smoothRoll
        self.previousP = smoothPitch
        previousY = smoothYaw
        self.previousTime = currTime

        # For Testing
        self.smoothYawAll.append(yaw)

        return [smoothRoll,smoothPitch,smoothYaw, self.timeAtRoll,self.timeAtPitch,self.timeAtYaw, rollMax ,rollFocus, pitchMax ,pitchFocus, yawMax ,yawFocus]


    # Real Time Exponential Moving Average Filter
    def rtSmoothFilter(self,prevRPY,rpyData, avgWeighting):
        smoothedData = rpyData*avgWeighting + (1-avgWeighting)*prevRPY
        return smoothedData


    def timeAtAngle(self,roll,pitch,yaw):
        # Assumption: All timesteps are close to the average time step
        
        # Corrects for the fact that RPY range is between 180 and -180
        roll += 180
        pitch += 180
        yaw += 179

        self.timeAtRoll[int(roll)] += 1
        self.timeAtPitch[int(pitch)] += 1
        self.timeAtYaw[int(yaw)] += 1


    # Calculates the approximate orientation that the head needs to be oriented in order to be facing the
    # operating field and calculates the percentage of time the head is facing that way (for the pitch orientation)
    # Assumption: The head needs to be facing downwards to see the operating table
    # Warning: This is a highly rudimentary algorithm.
    # the operating table

    # Finds operating angle by finding  the angle that takes the max time
    # The roll reading will most likely be impractical in the operating room
    def percentFocus(self,angles,RPYtype):
        # angles, angleDist, totalTime

        # acceptableRange is the range about a central angle that is allowed to count as
        # still facing the operating table
        # 5 is a dummy value that is overwritten
        acceptableRange = 5

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
        # Check if this is right
        totSamples = self.trialNum - self.calibrationNo

        operateAngle = np.argmax(angles)
        timeTarget = 0              # Time facing the target operating field
        for i in range(2*acceptableRange):
            iterAngle = operateAngle + i - acceptableRange

            # Need to rewrite so that it wraps around -------------------------XXXXXXXXXXXXXXX
            if(iterAngle < 0 or iterAngle > 360):
                continue
            else:
                timeTarget += angles[iterAngle]

        return [operateAngle, timeTarget/(self.trialNum-self.calibrationNo)]



    def plotter(self):
        pl.figure(1)
        pl.subplot(411)
        pl.plot(self.timeAtRoll)
        pl.subplot(412)
        pl.plot(self.timeAtPitch)
        pl.subplot(413)
        pl.plot(self.timeAtYaw)
        pl.subplot(414)
        pl.plot(self.smoothYawAll[0:])
        pl.show()

# #------------------------Blink Sensor Functions--------------------------
# '''BEN: This is the function that does some custom settings for the serial connection with the Arduino.
# It also starts the csv file where my data will be saved. usb is defined in the main function at the bottom.
# I think you should be able to merge any of your custom functions for the serial connection in with my function.'''
# #Set port and baudRate when calling this function
# def initSerialConnection(usb):
#     usb.timeout = 1
    
#     #This hopefully resets the Arduino
#     usb.setDTR(False)
#     #Was breaking
#     #time.sleep(1)
#     usb.flushInput()
#     usb.setDTR(True)
    
#     buffer = ''

#     #Writes the first line of both files
#     self.csv_writer(["AcclX","AcclY","AcclZ","MagX","MagY","MagZ","GyroX","GyroY","GyroZ", "Roll", "Pitch", "Yaw", "Time Elapsed(s)"],filenameIMU)


#------------------------Main Function-----------------------------------


# serialData = [isSuccess,[IR, AcclX,AcclY,AcclZ,MagX,MagY,MagZ,GyroX,GyroY,GyroZ,roll,pitch,yaw]

# if __name__=='__main__':

#     #Writes the raw data for the blink sensor
#     filename = raw_input('Enter a file name:  ')+ ".csv"
#     #Writes the raw data for the IMU
#     filenameIMU = (filename[:-4] + 'IMU.csv' )
#     #Reads the data to process for the blink sensor
#     filenameBlink = (filename[:-4] + 'Blink.csv' )

#     usb = Serial('COM6', 57600)
#     blinkSensor = bs.BlinkSensor()
#     blinkSensor.CheckKeyPress = False
#     blinkSensor.filename = filenameBlink
#     bs.initSerialConnection(usb, blinkSensor)
#     self.csv_writer(["AcclX","AcclY","AcclZ","MagX","MagY","MagZ","GyroX","GyroY","GyroZ", "Roll", "Pitch", "Yaw", "Time Elapsed(s)"],filenameIMU)
    
#     '''BEN: This is the loop I'm using right now to keep getting serial data and 
#     then save it to a usb when the user hits ctrl-c (or keyboard interrupts the shell)'''
#     while True:
#         try:
#             serialData = self.receiveSerial()

#             #Ensures that no errors are in the serialData array
#             #serialData[0] == 1 means that there were no failures
#             #serialData[0] == 0 means there was at least one failure
#             if(serialData[0] == 1):
#                 #[roll, pitch, yaw, currTime]
#                 IMUData = calcRPYData(serialData[1])
#                 # Checks to see if the calibration period has ended
#                 if(IMUData[4] == 1):
#                     processedData = processIMUData(IMUData)

#                     try:
#                        IR1 = float((serialData[1])[0])
#                        blinkSensor.Algorithm(IR1, False)
#                     except ValueError:
#                        print "Value Error"

#                     # Slows down the cycle enough to prevent divide by zero errors
#                     tm.sleep(.001)

#         except KeyboardInterrupt:  
#             plotter()
#             usb.close()
#             blinkSensor.saveFile()
#             # Remove for the real code
#             blinkSensor.csv_reader(1)
#             usb.close()
#             break
            






    

#------------------------Functions-------------------------------

#YO TEAM!!!
#You must ALWAYS type usb.close() after you keyboard interrupt the code to quit
#otherwise you'll be forced to unplug and replug the sensor

#The function writes a comma-delimited row of data into the file "filename"
#When opening the csv file, remember to select the delimiter as commas
#(open office is stupid and won't put the data in separate columns otherwise)

        
#Reads the comma-delimited csv file and writes it to lists.
#Then plots the lists.
# def csv_reader(nameOfFile):
#     with open(nameOfFile, 'r') as csv_file:
#         reader = csv.reader(csv_file, delimiter = ',')

#         GyroYTot = [];
#         RollTot = [];
#         PitchTot = [];
#         YawTot = [];
#         timeTot = [];

#         # Skips the first line which does not contain data
#         next(reader)
#         # Skips the calibration sequence to arrive at relevant
#         # RPY data
#         for i in range(self.calibrationNo):
#             next(reader)
#         #Creates a list for RPY and time from the
#             #csv file
#         for row in reader:
#             GyroYTot.append(float(row[7]))
#             RollTot.append(float(row[9]))
#             PitchTot.append(float(row[10]))
#             YawTot.append(float(row[11]))
#             timeTot.append(float(row[12]))

#         totalOpTime = max(timeTot) - min(timeTot)
#         print "Average Sampling Frequency: "
#         print len(timeTot)/totalOpTime
            
#         #Applies the moving average
#         smoothRoll = avgFilter(RollTot)
#         smoothPitch = avgFilter(PitchTot)
#         smoothYaw = avgFilter(YawTot)

#         #Find the time spent at each angle
#         [rollAngleList, rollDist] = self.timeAtAngle(timeTot,smoothRoll)
#         [pitchAngleList, pitchDist] = self.timeAtAngle(timeTot,smoothPitch)
#         [yawAngleList, yawDist] = self.timeAtAngle(timeTot,smoothYaw)

#         # Integrates the Gyroscope Data
#         gyroYaw = calcGyroYaw(timeTot, GyroYTot)
#         smoothGyro = avgFilter(gyroYaw)
#         [gyroYawList, gyroYawDist] = self.timeAtAngle(timeTot,smoothGyro)

#         #Calculate time spent looking at operating table(in Pitch angles)
#         [self.percentFocused, focusAngle] = detectTablePitch(pitchAngleList, pitchDist, totalOpTime)
#         print "Percent Time Focused in Pitch Angles: "
#         print self.percentFocused * 100
#         print "at Pitch angle of: "
#         print focusAngle

#         # Uses Gyro Data to calculate the Yaw angle for percent focusing
#         [self.percentFocused, focusAngle]= detectTableYaw(gyroYawList, gyroYawDist, totalOpTime)
#         print "Percent Time Focused in Yaw Angles: "
#         print self.percentFocused * 100
#         print "at Yaw angle of: "
#         print focusAngle
        
#         pl.rcParams.update({'font.size': 18})
#         #Plots the RPY data in a 3x1 figure with titles
#         pl.figure(1)
#         pl.subplot(421)
# ##        pl.plot(timeTot,RollTot)
#         pl.plot(timeTot,smoothRoll)
#         pl.xlabel("Time(s)")
#         pl.ylabel("Degrees")
#         pl.title("Roll")
        
#         pl.subplot(423)
# ##        pl.plot(timeTot,PitchTot)
#         pl.plot(timeTot,smoothPitch)
#         pl.xlabel("Time(s)")
#         pl.ylabel("Degrees")
#         pl.title("Pitch")
        
# ##        pl.subplot(425)
# ####        pl.plot(timeTot,YawTot)
# ##        pl.plot(timeTot,smoothYaw)
# ##        pl.xlabel("Time(s)")
# ##        pl.ylabel("Degrees")
# ##        pl.title("Yaw calculated with Magnetometer")
        
#         pl.subplot(422)
#         pl.plot(rollAngleList,rollDist)
#         pl.title("Time spent with head at Roll angle")
#         pl.ylabel("Time(s)")
#         pl.xlabel("Degrees of Rotation(Degees)")

#         pl.subplot(424)
#         pl.plot(pitchAngleList,pitchDist)
#         pl.title("Time spent with head at Pitch angle")
#         pl.ylabel("Time(s)")
#         pl.xlabel("Degrees of Rotation(Degees)")
# ##
# ##        pl.subplot(526)
# ##        pl.plot(yawAngleList,yawDist)
# ##        pl.title("Time spent with head at Yaw angle")
# ##        pl.ylabel("Time(s)")
# ##        pl.xlabel("Degrees of Rotation(Degees)")

#         pl.subplot(425)
# ##        pl.plot(timeTot,gyroYaw)
#         pl.plot(timeTot,smoothGyro)
#         pl.title("Yaw")
#         pl.xlabel("Time(s)")
#         pl.ylabel("Degrees")

#         pl.subplot(426)
#         pl.plot(gyroYawList,gyroYawDist)
#         pl.title("Time spent with head at Yaw angle")
#         pl.ylabel("Time(s)")
#         pl.xlabel("Degrees of Rotation(Degees)")

#         pl.subplot(427)
#         pl.plot(timeTot,GyroYTot)
#         pl.title("Anglular velocity from the Gyro")
#         pl.xlabel("Time(s)")
#         pl.ylabel("Angular Velocity(Deg/s)")

#         pl.subplots_adjust(hspace=0.69)
#         pl.show()


# #Applies a moving average filter
# def avgFilter(imuSignal):
#     global avgSize            #Determines the size of the avg filter
#     sigSize = len(imuSignal)
#     #Applies moving average
#     smoothSig = np.convolve(imuSignal, np.ones(avgSize)/avgSize, mode='same')
#     #Sets the first and last few smoothed values to
#     for i in range(avgSize):
#         smoothSig[i]=smoothSig[avgSize]
#         smoothSig[sigSize - 1 - i] = smoothSig[sigSize - 1 - avgSize]
#     return smoothSig


# Calculates the approximate orientation that the head needs to be oriented in order to be facing the
# operating field and calculates the percentage of time the head is facing that way (for the pitch orientation)
# Assumption: The head needs to be facing downwards to see the operating table
# Warning: This is a highly rudimentary algorithm.
# the operating table
# acceptableRange is the range about the angle that still counts as facing the table

# Finds operating angle by finding  the angle that takes the max time
# def detectTablePitch(angles, angleDist, totalTime):
#     global self.ACCEPTABLE_PITCH_RANGE
#     global MAX_OP_INCLINE           
#     minAngle = min(angles)
#     indexMin = 0
#     maxAngle = max(angles)
#     indexMax = len(angles)-1

#     if(angles.count(MAX_OP_INCLINE) != 0):
#         locZero = angles.index(MAX_OP_INCLINE)
#         operateAngle = np.argmax(angleDist[0:locZero])

#         timeTarget = 0              # Time facing the target operating field
#         for i in range(2*self.ACCEPTABLE_PITCH_RANGE):
#             iterAngle = operateAngle + i - self.ACCEPTABLE_PITCH_RANGE
#             # Ensures that the angle lies within the array
#             if(iterAngle < indexMin or iterAngle > indexMax):
#                 continue
#             else:
#                 # Accumulate all time values within the acceptable range about the calculated center
#                 # of operating table
#                 timeTarget += angleDist[angles[iterAngle]-minAngle]
                
#         return [timeTarget/totalTime, operateAngle+minAngle]
#     else:
#         return [0, 0]

# # Finds operating angle by finding  the angle that takes the max time
# def detectTableYaw(angles, angleDist, totalTime):
#     global self.ACCEPTABLE_YAW_RANGE
    
#     minAngle = min(angles)
#     indexMin = 0
#     maxAngle = max(angles)
#     indexMax = len(angles)-1
#     operateAngle = np.argmax(angleDist)

#     timeTarget = 0              # Time facing the target operating field
#     for i in range(2*self.ACCEPTABLE_YAW_RANGE):
#         iterAngle = operateAngle + i - self.ACCEPTABLE_YAW_RANGE
#         # Ensures that the angle lies within the array
#         if(iterAngle < indexMin or iterAngle > indexMax):
#             continue
#         else:
#             # Accumulate all time values within the acceptable range about the calculated center
#             # of operating table
#             timeTarget += angleDist[angles[iterAngle]-minAngle]
            
#     return [timeTarget/totalTime, operateAngle+minAngle]
    

