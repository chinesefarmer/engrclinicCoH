import csv
from serial import *
from math import *
import msvcrt as m
import numpy as np
import pylab as pl

#import datetime
#import time

from datetime import *
import Spring_BlinkSensor

#----------Global Variables for the IMU--------------------------------
# Customizable Parameters
avgSize = 30                    # Moving Average Filter Sample Size
avgWeighting = 0.5
pauseCheck = 0                                 # Debug code
SAMPLE_LENGTH = 2500
ACCEPTABLE_PITCH_RANGE = 5      #Max Possible Pitch angle and still be facing the table 
ACCEPTABLE_YAW_RANGE = 3
MAX_OP_INCLINE = 0
calibrationNo = 100             # Number of iterations during calibration step

# Required for some functions
trialNum = 0;
nextR = 0; nextP = 0; nextY = 0; 
gyroDriftX = 0; gyroDriftY = 0; gyroDriftZ = 0

previousR = 0;
previousP = 0;
previousY = 0;
previousTime = 0;
#---------------------------------------------------------------------

#--------Global Variables for the Blink Sensor--------------------------
CheckKeyPress = False
IRVector = []
tVector = []
derivVector = []
blinkVector = []
subBlink = []
debug = False
tWindow = 1.0/3
tPrintBlink = 1.0/6
minutes = 0
timeStamp = datetime.now().time()
startTime = (timeStamp.hour*60 + timeStamp.minute + (timeStamp.second + 0.000001*timeStamp.microsecond)/60)*60

#Length of running average
n=4
trackPos = False
trackNeg = False
startIR = 0
startIndex = 0
endIndex = 0
startT = 0
endT = 0
endIR = 0
peak = 0
valley = 0
blinkRange = []
negB = False
posB = False
positive = 0
negative = 0
#Running average of derivatives
runningAvg = 0
error = 0;

#Any derivatives above/below these values are considered part of a blink
negSlopeThresh = -23000
posSlopeThresh = 13000



#------------------------Functions-------------------------------

#YO TEAM!!!
#You must ALWAYS type usb.close() after you keyboard interrupt the code to quit
#otherwise you'll be forced to unplug and replug the sensor

#The function writes a comma-delimited row of data into the file "filename"
#When opening the csv file, remember to select the delimiter as commas
#(open office is stupid and won't put the data in separate columns otherwise)
def csv_writer(data,nameOfFile):
    with open(nameOfFile, 'a') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        writer.writerow(data)
        
#Reads the comma-delimited csv file and writes it to lists.
#Then plots the lists.
def csv_reader(nameOfFile):
    with open(nameOfFile, 'r') as csv_file:
        reader = csv.reader(csv_file, delimiter = ',')

        GyroYTot = [];
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
            GyroYTot.append(float(row[7]))
            RollTot.append(float(row[9]))
            PitchTot.append(float(row[10]))
            YawTot.append(float(row[11]))
            timeTot.append(float(row[12]))

        totalOpTime = max(timeTot) - min(timeTot)
        print "Average Sampling Frequency: "
        print len(timeTot)/totalOpTime
            
        #Applies the moving average
        smoothRoll = avgFilter(RollTot)
        smoothPitch = avgFilter(PitchTot)
        smoothYaw = avgFilter(YawTot)

        #Find the time spent at each angle
        [rollAngleList, rollDist] = timeAtAngle(timeTot,smoothRoll)
        [pitchAngleList, pitchDist] = timeAtAngle(timeTot,smoothPitch)
        [yawAngleList, yawDist] = timeAtAngle(timeTot,smoothYaw)

        # Integrates the Gyroscope Data
        gyroYaw = calcGyroYaw(timeTot, GyroYTot)
        smoothGyro = avgFilter(gyroYaw)
        [gyroYawList, gyroYawDist] = timeAtAngle(timeTot,smoothGyro)

        #Calculate time spent looking at operating table(in Pitch angles)
        [percentFocused, focusAngle] = detectTablePitch(pitchAngleList, pitchDist, totalOpTime)
        print "Percent Time Focused in Pitch Angles: "
        print percentFocused * 100
        print "at Pitch angle of: "
        print focusAngle

        # Uses Gyro Data to calculate the Yaw angle for percent focusing
        [percentFocused, focusAngle]= detectTableYaw(gyroYawList, gyroYawDist, totalOpTime)
        print "Percent Time Focused in Yaw Angles: "
        print percentFocused * 100
        print "at Yaw angle of: "
        print focusAngle
        
        pl.rcParams.update({'font.size': 18})
        #Plots the RPY data in a 3x1 figure with titles
        pl.figure(1)
        pl.subplot(421)
##        pl.plot(timeTot,RollTot)
        pl.plot(timeTot,smoothRoll)
        pl.xlabel("Time(s)")
        pl.ylabel("Degrees")
        pl.title("Roll")
        
        pl.subplot(423)
##        pl.plot(timeTot,PitchTot)
        pl.plot(timeTot,smoothPitch)
        pl.xlabel("Time(s)")
        pl.ylabel("Degrees")
        pl.title("Pitch")
        
##        pl.subplot(425)
####        pl.plot(timeTot,YawTot)
##        pl.plot(timeTot,smoothYaw)
##        pl.xlabel("Time(s)")
##        pl.ylabel("Degrees")
##        pl.title("Yaw calculated with Magnetometer")
        
        pl.subplot(422)
        pl.plot(rollAngleList,rollDist)
        pl.title("Time spent with head at Roll angle")
        pl.ylabel("Time(s)")
        pl.xlabel("Degrees of Rotation(Degees)")

        pl.subplot(424)
        pl.plot(pitchAngleList,pitchDist)
        pl.title("Time spent with head at Pitch angle")
        pl.ylabel("Time(s)")
        pl.xlabel("Degrees of Rotation(Degees)")
##
##        pl.subplot(526)
##        pl.plot(yawAngleList,yawDist)
##        pl.title("Time spent with head at Yaw angle")
##        pl.ylabel("Time(s)")
##        pl.xlabel("Degrees of Rotation(Degees)")

        pl.subplot(425)
##        pl.plot(timeTot,gyroYaw)
        pl.plot(timeTot,smoothGyro)
        pl.title("Yaw")
        pl.xlabel("Time(s)")
        pl.ylabel("Degrees")

        pl.subplot(426)
        pl.plot(gyroYawList,gyroYawDist)
        pl.title("Time spent with head at Yaw angle")
        pl.ylabel("Time(s)")
        pl.xlabel("Degrees of Rotation(Degees)")

        pl.subplot(427)
        pl.plot(timeTot,GyroYTot)
        pl.title("Anglular velocity from the Gyro")
        pl.xlabel("Time(s)")
        pl.ylabel("Angular Velocity(Deg/s)")

        pl.subplots_adjust(hspace=0.69)
        pl.show()


#Applies a moving average filter
def avgFilter(imuSignal):
    global avgSize            #Determines the size of the avg filter
    sigSize = len(imuSignal)
    #Applies moving average
    smoothSig = np.convolve(imuSignal, np.ones(avgSize)/avgSize, mode='same')
    #Sets the first and last few smoothed values to
    for i in range(avgSize):
        smoothSig[i]=smoothSig[avgSize]
        smoothSig[sigSize - 1 - i] = smoothSig[sigSize - 1 - avgSize]
    return smoothSig

# Creates a list of the angles and a list of the amount of time spent at those angles
def timeAtAngle(time,angle):
    # Assumption: All timesteps are close to the average time step
    avgTimeStep = (max(time)-min(time))/len(time)
    minAngle = int(min(angle))
    
    # Array of zeros with a fixed size equal to the total number of whole number angles
    angleTimes = np.zeros(int(max(angle))-minAngle + 1)
    timeAtAng = []

    # Creates a list with the amount of time spent at each angle (offset by the minumum angle)
    for i in range(len(angle)-1):
        currentAngle = int(angle[i])- minAngle
        angleTimes[currentAngle] += avgTimeStep
    # Creates a list of angle values that corresponds to the times above
    angleList = [x+minAngle for x in range(len(angleTimes))]

    return [angleList , angleTimes]

# Calculates the approximate orientation that the head needs to be oriented in order to be facing the
# operating field and calculates the percentage of time the head is facing that way (for the pitch orientation)
# Assumption: The head needs to be facing downwards to see the operating table
# Warning: This is a highly rudimentary algorithm.
# the operating table
# acceptableRange is the range about the angle that still counts as facing the table

# Finds operating angle by finding  the angle that takes the max time
def detectTablePitch(angles, angleDist, totalTime):
    global ACCEPTABLE_PITCH_RANGE
    global MAX_OP_INCLINE           
    minAngle = min(angles)
    indexMin = 0
    maxAngle = max(angles)
    indexMax = len(angles)-1

    if(angles.count(MAX_OP_INCLINE) != 0):
        locZero = angles.index(MAX_OP_INCLINE)
        operateAngle = np.argmax(angleDist[0:locZero])

        timeTarget = 0              # Time facing the target operating field
        for i in range(2*ACCEPTABLE_PITCH_RANGE):
            iterAngle = operateAngle + i - ACCEPTABLE_PITCH_RANGE
            # Ensures that the angle lies within the array
            if(iterAngle < indexMin or iterAngle > indexMax):
                continue
            else:
                # Accumulate all time values within the acceptable range about the calculated center
                # of operating table
                timeTarget += angleDist[angles[iterAngle]-minAngle]
                
        return [timeTarget/totalTime, operateAngle+minAngle]
    else:
        return [0, 0]

# Finds operating angle by finding  the angle that takes the max time
def detectTableYaw(angles, angleDist, totalTime):
    global ACCEPTABLE_YAW_RANGE
    
    minAngle = min(angles)
    indexMin = 0
    maxAngle = max(angles)
    indexMax = len(angles)-1
    operateAngle = np.argmax(angleDist)

    timeTarget = 0              # Time facing the target operating field
    for i in range(2*ACCEPTABLE_YAW_RANGE):
        iterAngle = operateAngle + i - ACCEPTABLE_YAW_RANGE
        # Ensures that the angle lies within the array
        if(iterAngle < indexMin or iterAngle > indexMax):
            continue
        else:
            # Accumulate all time values within the acceptable range about the calculated center
            # of operating table
            timeTarget += angleDist[angles[iterAngle]-minAngle]
            
    return [timeTarget/totalTime, operateAngle+minAngle]
    


# Will return 0 if the function fails to receive readable data from serial and
# will return 1 if the function succeeds
def receiveSerial():

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
                roll = 0
                pitch = 0
                yaw = 0
                serialData = [IR, AcclX,AcclY,AcclZ,MagX,MagY,MagZ,GyroX,GyroY,GyroZ,roll,pitch,yaw]
                return [1, serialData]
            except ValueError:
                return [0, serialData]
    return [0, serialData]


def calcRPYData(serialData):
    [IR1,AcclX,AcclY,AcclZ,MagX,MagY,MagZ,GyroX,GyroY,GyroZ,roll,pitch,yaw] = serialData
    #Initialize variables for requried roll, pitch, yaw calculations
    global trialNum, nextR, nextP, nextY, gyroDriftX, gyroDriftY, gyroDriftZ
    global calibrationNo
    global last_received
    global startTime
    # Calibration Sequence: Accounts for drift of gyro data
    # During calibration, the IMU must be placed on a stationary
    # surface
    if (trialNum < 5):
        trialNum = trialNum + 1
    elif(trialNum < calibrationNo - 1):
        trialNum = trialNum + 1
        gyroDriftX = gyroDriftX - GyroX
        gyroDriftY = gyroDriftY - GyroY
        gyroDriftZ = gyroDriftZ - GyroZ

    elif(trialNum == calibrationNo - 1):
        trialNum = trialNum + 1
        gyroDriftX = gyroDriftX / calibrationNo
        gyroDriftY = gyroDriftY / calibrationNo
        gyroDriftZ = gyroDriftZ / calibrationNo
    # Calibration Sequence completed
    else:

        #Pause initiated to allow users to secure the IMU on user's head
        global pauseCheck
        if(pauseCheck == 0):
            pauseCheck = 1
            #Should be replaced with GUI interrupt that triggers when
            #the IMU is secured
            raw_input("Please put on Headset, then press enter:")
  
        trialNum = trialNum + 1

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

        yawY = MagY*sin(roll) - MagZ*cos(roll)
        yawX = -MagX*cos(pitch)+ MagZ*sin(pitch)*sin(roll) + MagY*sin(pitch)*cos(roll)

        yawOffset = 0
        
        yaw = atan2(yawY, yawX)
        
        gX = abs(GyroX + gyroDriftX)
        gY = abs(GyroY + gyroDriftY)
        gZ = abs(GyroZ + gyroDriftZ)

        prevR = nextR
        prevP = nextP
        prevY = nextY

        nextR = (prevR + roll*gX) / (1 + gX)
        nextP = (prevP + pitch * gZ) / (1 + gZ)
        nextY = (prevY + yaw * gY) / (1 + gY)

        roll = nextR*180/pi
        pitch = -1*nextP*180/pi
        yaw = abs(nextY*180/pi)

    timeStamp = datetime.now().time()
    #Time elapsed from start
    currTime = ((timeStamp.hour*60 + timeStamp.minute + (timeStamp.second + 0.000001*timeStamp.microsecond)/60))*60 - startTime
    #Saves the IMU data to a csv file
    data = [AcclX, AcclY, AcclZ, MagX, MagY, MagZ, GyroX, GyroY, GyroZ, roll, pitch, yaw, currTime]
    csv_writer(data,filenameIMU)
    return [roll, pitch, GyroY ,currTime]

##    # Stops program after a number of samples have been collected
##    # Should be replaced with interrupt by GUI
##    global SAMPLE_LENGTH
##    if(trialNum >= SAMPLE_LENGTH):
##        # Plots the RPY data
##        csv_reader(filenameIMU)
##        break

def processIMUData(IMUData):
    global previousR, previousP, previousY
    [roll, pitch, gyroY, currTime] = IMUData
    smoothRoll = rtSmoothFilter(previousR, roll);
    smoothPitch = rtSmoothFilter(previousP, pitch);

    yaw = calcGyroYaw(currTime,previousY,gyroY)
    smoothYaw = rtSmoothFilter(previousY,yaw)

    previousR = smoothRoll
    previousP = smoothPitch
    previousY = smoothYaw
    previousTime = currTime

    return [smoothRoll,smoothPitch,smoothYaw]



# Real Time Exponential Moving Average Filter
def rtSmoothFilter(prevRPY,rpyData):
    global avgWeighting            #Determines the size of the avg filter
    smoothedData = rpyData*avgWeighting + (1-avgWeighting)*prevRPY
    return smoothedData


# #For Testing purposes
# def appendData(IMUData):


def calcGyroYaw(previousY, currTime, gyroY):
    global previousTime, gyroDriftY

    yawAngle = (((gyroY+gyroDriftY)*(currTime-previousTime)+previousY)*.998)

    return yawAngle

# Old Code
# def calcGyroYaw(timeTot, gyro):
#     yawAngle = [0]
#     yawAngle.append(0)
#     for i in range(1,len(gyro)-1):
#        yawAngle.append(((gyro[i]+gyroDriftY)*(timeTot[i]-timeTot[i-1])+yawAngle[i-1])*.998)

#     return yawAngle




                
#------------------------Blink Sensor Functions--------------------------
'''BEN: This is the function that does some custom settings for the serial connection with the Arduino.
It also starts the csv file where my data will be saved. usb is defined in the main function at the bottom.
I think you should be able to merge any of your custom functions for the serial connection in with my function.'''
#Set port and baudRate when calling this function
def initSerialConnection(usb):
    usb.timeout = 1
    
    #This hopefully resets the Arduino
    usb.setDTR(False)
    #Was breaking
    #time.sleep(1)
    usb.flushInput()
    usb.setDTR(True)
    
    buffer = ''

    #Writes the first line of both files
    csv_writer(["Y:D:M", "H:M:S", "Seconds","IR1"],filename)
    csv_writer(["AcclX","AcclY","AcclZ","MagX","MagY","MagZ","GyroX","GyroY","GyroZ", "Roll", "Pitch", "Yaw", "Time Elapsed(s)"],filenameIMU)


#------------------------Main Function-----------------------------------




# serialData = [isSuccess,[IR, AcclX,AcclY,AcclZ,MagX,MagY,MagZ,GyroX,GyroY,GyroZ,roll,pitch,yaw]

if __name__=='__main__':

    global filename,filenameIMU,outputFile
    #Writes the raw data for the blink sensor
    filename = raw_input('Enter a file name:  ')+ ".csv"
    #Writes the raw data for the IMU
    filenameIMU = (filename[:-4] + 'IMU.csv' )
    #Reads the data to process for the blink sensor
    outputFile = (filename[:-4] + 'Full.csv' )

    usb = Serial('COM6', 57600)
    initSerialConnection(usb)
    '''BEN: This is the loop I'm using right now to keep getting serial data and 
    then save it to a usb when the user hits ctrl-c (or keyboard interrupts the shell)'''
    while True:
        try:
            serialData = receiveSerial()
            #Ensures that no errors are in the serialData array
            #serialData[0] == 1 means that there were no failures
            #serialData[0] == 0 means there was at least one failure
            if(serialData[0] == 1):
                #[roll, pitch, yaw, currTime]
                IMUData = calcRPYData(serialData[1])
                processedData = processIMUData(IMUData)
                # appendData(processedData)


#                print (serialData[1])[0]
#                blinkAlgorithm((serialData[1])[0])

            # getSerial(usb)
        except KeyboardInterrupt:
            csv_reader(filenameIMU)
            # saveFile(usb)
            # csv_reader(outputFile)
            break
            






    
