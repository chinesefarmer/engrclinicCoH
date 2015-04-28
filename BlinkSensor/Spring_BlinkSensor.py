import csv
import math
from serial import *
from datetime import *
import time
import pylab as pl
from KeyPress import *
import numpy as np
debug = False
test = True


'''
Resets and initializes the connection with the Arduino. Also creates the csv file where
the data will be saved later.
Inputs: usb (the serial connection including the port and baudrate)
        BlinkSensor (the initialized BlinkSensor class that holds all the algorithm info)
Outpus: None
'''
def initSerialConnection(usb, BlinkSensor):
    #Sets a 1ms pause between collecting data points
    usb.timeout = 1
    
    #Resets the Arduino
    usb.setDTR(False)
    time.sleep(1)
    usb.flushInput()
    usb.setDTR(True)
    
    buffer = ''
    #Clears and overwrites the text file that will contain the detected blinks
    BlinkSensor.saveBlinks([],1)
    #The csv file will save the times where actual blinks occurred if you set CheckKeyPress
    #to True, meaning you are running both this script and KeyPress.py at the same time
    if BlinkSensor.CheckKeyPress == True:
        BlinkSensor.csv_writer(["Hour","Minute","Second","IR1","Blinks", "Actual Blinks"], 1)
    else:
        BlinkSensor.csv_writer(["Hour","Minute","Second","IR1","Blinks"], 1)


'''
Gets the next IR value from the Arduino serial connection and sends it to the blink detection
algorithm.
Inputs: usb (the serial connection including the port and baudrate)
        BlinkSensor (the initialized BlinkSensor class that holds all the algorithm info)
Outpus: None
'''
def getSerial(usb, BlinkSensor):
    global debug
    buffer = usb.readline()
        
    if '\n' in buffer:
        lines = buffer.split('\n')
        IR1 = lines[-2]
        if '\r' in IR1:
            IR1Bogus = IR1.split('\r')
            if len(IR1Bogus) > 12:
                print "Error"
            else:
                #Sometimes the sensor will not send a value or send something that's not possible
                #to turn into a float 
                try:
                    IR1 = float(IR1Bogus[0])
                    BlinkSensor.Algorithm(IR1, False)
                except ValueError:
                    print "Value Error"
                    
        else:
            try:
                IR1 = float(IR1)
                BlinkSensor.Algorithm(IR1, False)
            except ValueError:
                print "Value Error"

'''
Blink Sensor class containing the following methods:
    clearParameters
    csv_writer
    Algorithm
    PeakAlgorithm
    ValleyAlgorithm
    saveBlinks
    openBlinks
    saveFile
    addBlinksinWindow
    updateBlinksinWindow
    csv_reader

'''
class BlinkSensor:
    def __init__(self):
        #The following are parameters that change what the algorithm defines as a blink
        #For a blink that looks like a valley, the negative slope must be less than:
        self.negSlopeThresh = -8500
        #For a blink that looks like a peak, the positive slope must be greater than:
        self.posSlopeThresh = 6700
        #The peak must be at least this tall to be considered a blink and not noise
        self.PeakBlinkHeight = 399
        #The valley must be at least this deep to be considered a blink and not noise
        self.ValleyBlinkHeight = 400

        #How often to calculate the number of blinks, in minutes
        self.tWindow = 1.0/3
        #How often to print number of blinks in last X minutes, where X is tWindow
        self.tPrintBlink = 1.0/6
        
        #The name of the file where the data is saved while the blink sensor is being run live
        #at the end of the trial it is saved to filename
        self.bogusFile = 'bogus.csv'
        #Name of the file to save the data in
        self.filename = ''
        #Name of the file to save data in when test mode is turned on
        self.testFileName = ''
        #Set equal to True if you are running KeyPress.py at the same time to record when the
        #blinks are actually occurring.
        self.CheckKeyPress = False
        #Vector that holds the raw IR LED values
        self.IRVector = []
        #Vector that holds time values in seconds, used for the algorithm calculations
        self.secVector = []
        #Vector that holds time values in minutes (the current hour, minute, and second are converted into minutes)
        #this is used to determine how often to print out the blink rate
        self.minVector = []
        #Vector containing blink data for the number of blinks in the last X minutes, where X is tWindow
        self.subBlink = []
        #The current time expressed in minutes
        self.minutes = 0
        timeStamp = datetime.now().time()
        #Used for keeping track of the starting time value of the subBlink vector
        self.startTime = (timeStamp.hour*60 +
                          timeStamp.minute +
                          (timeStamp.second + 0.000001*timeStamp.microsecond)/60)
        #How often there has to be a positive or negative slope fitting the thresholds for it to be considered a blink
        self.n=4
        #Algorithm sets to True if posSlopeThresh has been triggered meaning there might be a blink
        self.lookForPeak = False
        #Algorith sets to True if negSlopethresh has been triggered meaning there might be a blink
        self.lookForValley = False
        #The IR value at the beginning of what the algorithm thinks is a blink, used to determine the blink's height
        self.startIR = 0
        #The IR value at the end of what the algorithm thinks is a blink, used to determine the blink's height
        self.endIR = 0
        #Blink's starting time in seconds (used for saving the blink into the csv)
        self.blinkStartSec = 0
        #Blink's starting time in minutes (used for printing out the blink rate)
        self.blinkStartMinutes = 0
        #Blink's ending time in seconds (used for saving the blink into the csv)
        self.blinkEndSec = 0
        #Blink's ending time in minutes (used for printing out the blink rate)
        self.blinkEndMinutes = 0
        #IR value of the blink's peak, used for calculating the blink's height
        self.peak = 0
        #IR value of the blink's valley, used for calculating the blink's depth
        self.valley = 0
        #There was previously a trend of negative slopes in the PeakAlgorithm
        self.negativeSlope = False
        #There was previously a trend of positive slopes in the ValleyAlgorithm
        self.positiveSlope = False
        #Incremented if the slope isn't steep enough to be considered part of the blink.
        self.possibleFalseNegativeSlope = 0
        #Incremented in ValleyAlgorithm if there's been a positive slope, meaning we're coming up from a valley blink
        self.positive = 0
        #Inremented in PeakAlgorithm if there's been a negative slope, meaning we're coming down from the peak blink
        self.negative = 0
        #Number of actual blinks when KeyPress.py is also being run
        self.ActualBlinks = 0
        #How many of the detected blinks were actual blinks
        self.MatchedBlinks = 0
        #Number of detected blinks
        self.DetectedBlinks = 0
        #the time in seconds of one cell of the saved excel file set by testMainFn.py (test mode)
        self.timeTestMode = 0
        #the time in minutes of one cell of the saved excel file set by testMainFn.py (test mode)
        self.minTestMode = 0
        #To keep track of how many IR values fall are above the positive threshold.
        #if this is below n when the code comes to the end of a blink, that means it was actually a
        #false alarm.
        self.negBlinkPoints = 0

    '''
    Clears variables every time a blink is detected so they are reset and ready for detecting new blinks
    Inputs:     i (the current index of the vectors)
    Outputs:    Nothing
    '''
    def clearParameters(self, i):
        self.blinkEndSec = 0
        self.blinkEndMinutes = 0
        self.endIR = 0
        self.lookForPeak = False
        self.lookForValley = False
        self.blinkStartMinutes = 0
        self.blinkStartSec = 0
        self.startIR = 0
        self.peak = 0
        self.valley = 0
        self.negBlinkPoints = 0
        self.positive = 0
        self.negative = 0
        self.negativeSlope = False
        self.positiveSlope = False
        self.lengthOfValley = 0
        self.possibleFalseNegativeSlope = 0
        
        #Clears out all except the two most recent values
        self.IRVector = self.IRVector[i-1:]
        self.secVector = self.secVector[i-1:]
        self.minVector = self.minVector[i-1:]
        

    '''
    Writes data to the bogus excel file as the blink sensor is running live.
    Inputs:     data (a vector in the form [hours, minutes, seconds, IR Value] containing the values for one row
                mode
                    1:           overwrites the bogusFile during a new blink sensor session
                    otherwise:   appends to the current bogusFile
    Outpus:     None
    '''
    def csv_writer(self,data, mode):
        if mode == 1:
            with open(self.bogusFile, 'w') as csv_file:
                writer = csv.writer(csv_file, delimiter=',')
                writer.writerow(data)
        else:
            with open(self.bogusFile, 'a') as csv_file:
                writer = csv.writer(csv_file, delimiter=',')
                writer.writerow(data)                         

    '''
    Blink detection algorithm, which is called each time a data point is received by the Teensie. Takes the
    derivative of the IR values, and if the values are steep enough (positive or negative wise) then the correct
    sub-algorithm is called
    Inputs:     IR1 (the current IR value, passed in by the parent function running the teensie connection
                testMode
                    True:   We aren't running the blink sensor live but getting time values from saved data
                    False:  The blink sensor is live, time stamps are achieved from the computer's clock
    Outputs:    Returns the number of blinks in the last X minutes, where X is determined by tWindow. It only
                returns the blink rate every tPrintBlink minutes, otherwise it returns 0
    '''
    def Algorithm(self,IR1,testMode):
        global debug
        global test
        if(testMode == False):
            #Get the current time ste[p
            timeD = datetime.now().time()
            #Appends times to vectors
            self.minutes = timeD.hour*60 + timeD.minute + (timeD.second + 0.000001*timeD.microsecond)/60
            seconds = (timeD.second + 0.000001*timeD.microsecond)
            self.secVector.append(seconds)
            self.minVector.append(self.minutes)

            #Calculates if tPrintBlink minutes have passed, meaning we need to print the blink rate again
            tDif = abs(self.minutes - self.startTime - self.tPrintBlink)

            self.UpdateBlinksInWindow()
        #In test mode the time vector is fed one value at a time by testMainFn based on the data in the excel file
        else:
            self.secVector.append(self.timeTestMode)
            self.minVector.append(self.minTestMode)
        self.IRVector.append(IR1)

        #If we're beyond the first data point...
        if(len(self.IRVector) > 1):
            i = len(self.IRVector)-1
            
            #Take the derivative
            deriv = (self.IRVector[i]-self.IRVector[i-1])/(self.secVector[i]-self.secVector[i-1])

            #If it's a positive slope above the threshold, start tracking
            if(self.lookForPeak):
                self.PeakAlgorithm(i, deriv)
            #If it's a negative slope below the threshold, start tracking
            elif(self.lookForValley):
                self.ValleyAlgorithm(i, deriv)

            #Checks to see if the current derivative triggers either threshold
            else:
                #May be dealing with a peak
                if(deriv >= self.posSlopeThresh):
                    #start tracking the slope!
                    if debug:
                        print ("Looking for peak at time: " + str(self.secVector[i-1])
                               + "after deriv: " + str(deriv))
                    self.lookForPeak = True
                    self.blinkStartSec = self.secVector[i-1]
                    self.blinkStartMinutes = self.minVector[i-1]
                    self.startIR = self.IRVector[i-1]
                    self.peak = self.IRVector[i-1]
                #May be dealing with a valley
                elif(deriv <= self.negSlopeThresh):
                    if debug:
                        print ("Looking for valley at time: " + str(self.secVector[i-1])
                               + "after deriv: " + str(deriv))
                    self.lookForValley = True
                    self.blinkStartSec = self.secVector[i-1]
                    self.blinkStartMinutes = self.minVector[i-1]
                    self.startIR = self.IRVector[i-1]
                    self.valley = self.IRVector[i-1]
                else:
                    self.clearParameters(i)
        #If we aren't using save data (not running live) then print the blink rate
        if(test == False):
            data = [str(timeD.hour),str(timeD.minute),str(timeD.second + 0.000001*timeD.microsecond),IR1]
            #Overwrites bogusFile to prepare for saving data
            self.csv_writer(data, 0)
            if(tDif < 10**-2):
                print 
                print "--------------------------------------------------"
                print (str(len(self.subBlink)) + " blinks in the last " +
                       str(round(self.tWindow,1)) + " minutes")
                print "--------------------------------------------------"
                print
                self.startTime = self.minutes
                return len(self.subBlink)
            else:
                return 0

    '''
    Algorithm to determine if the IR values are indicating a peak blink by checking against various thresholds
    Inputs:     i (the current index of the vectors, incremented every loop through the algorithm)
                deriv (the slope at the current index, sent by the Algorithm function)
    Outputs:    None
    '''
    def PeakAlgorithm(self,i, deriv):
        global debug
        #If the IRVal is greater than the previous peak, this is now considered the peak
        if(self.IRVector[i-1] > self.peak):
            self.peak = self.IRVector[i-1]
        #Has there been a trend of negative slopes but we just detected a positive slope?
        if(self.negativeSlope):
            if debug:
                print "Inside elif(negativeSlope) the deriv is "+str(deriv)+" and positive = "+str(self.positive)
            self.positive = self.positive + 1
            #We detected this positive slope after negative slopes more than 4 times
            if(self.positive > 4):
                self.blinkEndSec = self.secVector[i-2]
                self.blinkEndMinutes = self.minVector[i-2]
                self.endIR = self.IRVector[i-2]
                #The blink height greater than the PeakBlinkHeight threshold, meaning it's a blink
                if((self.peak-self.endIR) > self.PeakBlinkHeight and (self.peak-self.startIR) > self.PeakBlinkHeight):
                    if debug:
                        print "Ending time is: " + str(self.blinkEndSec)
                    self.saveBlinks([[self.blinkStartSec, self.blinkEndSec]],2)
                    self.AddBlinksInWindow([self.blinkStartMinutes, self.blinkEndMinutes])
                    if debug:
                        print "Blink from : " + str(self.blinkStartSec) + " sec to "+str(self.blinkEndSec)+" sec"
                    print "Length of blink: " + str(round((self.blinkEndSec-self.blinkStartSec),2)) + " sec"
                #The blink height isn't large enough, so it's not a blink
                else:
                    if debug:
                        print ("Peak ignored at " + str(self.secVector[i]) + " sec, height of: "+
                               str(self.peak-self.startIR) + "or "+str(self.peak-self.endIR) +
                               " not large enough, inside elif(negativeSlope)")
                #Whether blink or false alarm, clear the variables
                self.clearParameters(i)
        #The derivative is negative
        elif(deriv < 0):
            #The negative slope threshold hasn't been triggered, meaning it's a shallow negative slope, which
            #could occur when the blink is ending and flattening out.
            if(deriv > self.negSlopeThresh):
                if debug:
                    print "Nearing end of peak at "+str(self.secVector[i])+" sec w/ deriv "+ str(deriv)
                self.negative = self.negative + 1
                #There have been more than n+3 points in the negative slope of the blink peak
                if(self.negative > self.n+3):
                    self.blinkEndSec = self.secVector[i-2]
                    self.blinkEndMinutes = self.minVector[i-2]
                    self.endIR = self.IRVector[i-2]
                    #The blink height is greater than the PeakBlinkHeight threshold, meaning this is a blink
                    if((self.peak-self.endIR) > self.PeakBlinkHeight and
                       (self.peak-self.startIR) > self.PeakBlinkHeight):
                        self.saveBlinks([[self.blinkStartSec, self.blinkEndSec]],2)
                        self.AddBlinksInWindow([self.blinkStartMinutes, self.blinkEndMinutes])
                        if debug:
                            print "Blink from : " + str(self.blinkStartSec) + " sec to "+str(self.blinkEndSec)+" sec"
                        print "Length of blink: " + str(round((self.blinkEndSec-self.blinkStartSec),3)) + " sec"
                        
                    #The blink's height isn't large enough, so it's not a blink
                    else:
                        if debug:
                            height = min(self.peak-self.endIR,self.peak-self.startIR)
                            print ("Peak ignored at " + str(self.secVector[i]) +
                                   " sec, height of " + str(height)+" not large enough")
                    #Whether blink or false alarm, clear the variables
                    self.clearParameters(i)
                #The blink isn't over yet
                else:
                    self.possibleFalseNegativeSlope = self.possibleFalseNegativeSlope +1
                    #If there has been a negative derivative twice, then we are past the peak and coming down from
                    #the blink peak, so set negativeSlope to True
                    if(self.possibleFalseNegativeSlope > 2):
                        if debug:
                            print ("Switching from tracking pos to neg slope at " +str(self.secVector[i])
                                   +" sec with deriv "+str(deriv))
                        self.negativeSlope = True
            #The slope's not steep enough to be part of the downward slope of the peak
            else:
                #If a shallow negative slope occurs more than twice, set negativeSlope to True indicating there's
                #been a trend of negative slopes
                self.possibleFalseNegativeSlope = self.possibleFalseNegativeSlope +1
                if(self.possibleFalseNegativeSlope > 2):
                    if debug:
                        print ("Switching from tracking pos to neg slope at " +str(self.secVector[i])
                               +" sec with deriv "+str(deriv))
                    self.negativeSlope = True
                

    '''
    Algorithm to determine if the IR values are indicating a valley blink by checking against various thresholds
    Inputs:     i (the current index of the vectors, incremented every loop through the algorithm)
                deriv (the slope at the current index, sent by the Algorithm function)
    Outputs:    None
    '''
    def ValleyAlgorithm(self,i, deriv):
        global debug
        #If the IRVal is less than the previous value, this is now
        #considered the lowest point in the blink valley
        if(self.IRVector[i-1] < self.valley):
            self.valley = self.IRVector[i-1]
        #The derivative is positive
        if(deriv > 0):
            #If the derivative is less than the positive threshold, that means
            #we've likely flattened out
            if(deriv < self.posSlopeThresh):
                self.endIR = self.IRVector[i-2]
                if debug:
                    print "Nearing end of valley at "+str(self.secVector[i])+" sec"
                self.positive = self.positive + 1
                #If there's been a shallow positive slope for more than n-2 times but less than n-1 points in
                #the downard slope of the blink, then it isn't considered a blink
                if((self.positive > self.n-2) and (self.negBlinkPoints <= self.n-1)):
                    if debug:
                            print ("Blink ignored since only "+str(self.negBlinkPoints)+
                                   " points in the negative slope. Time stamp: "+  str(self.secVector[i]))
                    self.clearParameters(i)
                #The slope going into the blink smaller than the slope coming out of the blink
                elif((self.startIR - self.valley + 200) < (self.endIR - self.valley)):
                    if debug:
                        print ("Blink ignored since the exit slope is way higher than the entering slope" +
                               " meaning this might be the beginning of a peak blink, not valley at "+
                               str(self.secVector[i])+"sec")
                    self.clearParameters(i)
                #There's been a positive slope for n times and the blink depth greater than the ValleyBlinkHeight
                #threshold
                elif((self.positive > self.n) and (self.endIR - self.valley > self.ValleyBlinkHeight )
                   and ((self.startIR - self.valley) > self.ValleyBlinkHeight)):
                    self.blinkEndSec = self.secVector[i-2]
                    self.blinkEndMinutes = self.minVector[i-2]
                    self.endIR = self.IRVector[i-2]
                    #There's more than n-1 points in the negative slope of the blink, meaning that it is a blink
                    if(self.negBlinkPoints >= self.n-1):
                        if debug:
                            print "Ending time is: " + str(self.blinkEndSec)
                        self.saveBlinks([[self.blinkStartSec, self.blinkEndSec]],2)
                        if debug:
                            print "Blink from : " + str(self.blinkStartSec) + " sec to "+str(self.blinkEndSec)+" sec"
                        print "Length of blink: " + str(round((self.blinkEndSec-self.blinkStartSec),2)) + " sec"
                        self.AddBlinksInWindow([self.blinkStartMinutes, self.blinkEndMinutes])
                    #There aren't enough points in the negative slope, so this isn't a blink
                    else:
                        if debug:
                            print ("Blink ignored since only "+str(self.negBlinkPoints)+
                                   " points in the negative slope. Time stamp: "+  str(self.secVector[i]))

                    self.clearParameters(i)

                #There's been a positive slope, but the blink may not be over yet
                else:
                    if(self.positive > 2):
                        self.positive = self.positive + 1
                    self.positiveSlope = True
            #The slope is steep enough to have triggered the threshold
            else:
                self.endIR = self.IRVector[i-2]
                #The slope going into the blink is smaller than the slope coming out of the blink, meaning
                #it's not a blink
                if((self.startIR - self.valley + 200) < (self.endIR - self.valley)):
                    if debug:
                        print ("Blink ignored since the exit slope is way higher than the entering slope" +
                               " meaning this might be the beginning of a peak blink, not valley at "+
                               str(self.secVector[i])+"sec")
                    self.clearParameters(i)
                #If there has been a positive slope more than n-2 times, but there are less than n-1 points in
                #the negative slope, then this isn't a blink
                elif((self.positive > self.n-2) and (self.negBlinkPoints <= self.n-1)):
                    if debug:
                            print ("Blink ignored since only "+str(self.negBlinkPoints)+
                                   " points in the negative slope. Time stamp: "+  str(self.secVector[i]))
                    self.clearParameters(i)
                #there's been a history of positive slopes, so set positiveSlope to True
                else:
                    self.positiveSlope = True
        #If the slope is negative after we've been coming out of the valley, that
        #means the blink is over. positiveSlope just means that previously there was a trend of a positive
        #slopes, so if for some reason the slope is negative again, that means the blink is over.
        elif(self.positiveSlope):
            #Wait to get multiple negative slopes to ensure this isn't a false alarm
            if(self.negative == 0):
                self.negative = 1
            elif(self.negative == 1):
                self.negative = 2
            else:
                self.blinkEndSec = self.secVector[i-2]
                self.blinkEndMinutes = self.minVector[i-2]
                self.endIR = self.IRVector[i-2]
                #The blink depth is greater than the ValleyBlinkHeight threshold
                if((self.endIR - self.valley) > self.ValleyBlinkHeight and (self.startIR - self.valley) > self.ValleyBlinkHeight):
                    #There are more than n-1 points in the negative slope, meaning it's a blink
                    if(self.negBlinkPoints >= self.n-1):
                        if debug:
                            print "Ending time is: " + str(self.blinkEndSec)
                        self.saveBlinks([[self.blinkStartSec, self.blinkEndSec]],2)
                        if debug:
                            print "Blink from : " + str(self.blinkStartSec) + " sec to "+str(self.blinkEndSec)+" sec"
                        print "Length of blink: " + str(round((self.blinkEndSec-self.blinkStartSec),2)) + " sec"
                        self.AddBlinksInWindow([self.blinkStartMinutes, self.blinkEndMinutes])
                    #There aren't enough points in the negative slope, so it isn't a blink
                    else:
                         if debug:
                             print "Blink ignored since only "+str(self.negBlinkPoints)+" points in the negative slope. Time stamp: "+  str(self.secVector[i])
                #The height isn't large enough, so it isn't a blink
                else:
                    if debug:
                        print "Valley ignored at " + str(self.secVector[i]) + " sec, height not large enough"

                self.clearParameters(i)
        #It's just another point in the downward slope of the valley blink, so increment negBlinkPoints
        else:
            self.negBlinkPoints = self.negBlinkPoints + 1

    '''
    Saves blinks into the Blinks.txt file. This function is called by PeakAlgorithm and ValleyAlgorithm
    Inputs:     blinks (vector in the form [blink starting time, blink ending time]
                mode
                    1:  called when initializing the blink sensor to clear out and overwrite the old Blinks.txt file
                    2:  appends the blink to a new line in the Blinks.txt file
    Outpus:     None
    '''
    def saveBlinks(self,blinks,mode):
        if mode == 1:
            with open('Blinks.txt','w') as myfile:
                myfile.write("\n")
                myfile.close()
        elif mode ==2:
            with open('Blinks.txt','a') as myfile:
                myfile.write("\n")
                myfile.write("\n".join(map(lambda x: (str(x[0]) + ', ' + str(x[1])),blinks)))
                myfile.close()

    '''
    Reads the blinks from the Blinks.txt file and puts them into the blinkArray. This is called by saveFile.
    Inputs:     None
    Outputs:    blinkArray (a vector containing all the blinks, with each blink in the form
                [blink starting time, blink ending time])
    '''
    def openBlinks(self):
        blinkTextFile = open('Blinks.txt','r')
        lines = blinkTextFile.read().split('\n')
        strArray = map(lambda x: x.split(', '), lines)
        #Removes the blank line at the top of the file
        strArray = strArray[2:]
        blinkArray = map(lambda x: [float(x[0]), float(x[1])], strArray)
        return blinkArray
    
    '''
    Reads data from bogusFile, and writes it and the blinks into a new excel file called filename. It will also
    write to a column named "Actual Blinks" if you ran KeyPress.py at the same time
    Inputs:     None
    Outputs:    None
    '''
    def saveFile(self):
        global debug
        keyPressVector = []
        if self.CheckKeyPress:
            keyPressVectorNp = np.load('KeyPress.npy')
            keyPressVector = keyPressVectorNp.tolist()
            print "Key Press Vector: " + str(keyPressVector)
        blinkArray = self.openBlinks()
        if debug:
            print blinkArray
        self.DetectedBlinks = len(blinkArray)
        self.ActualBlinks = len(keyPressVector)

        with open(self.bogusFile, 'rb') as input, open((self.filename), 'wb') as output:
            writer = csv.writer(output, delimiter=',')
            reader = csv.reader(input, delimiter = ',')
            blink = False
            all = []
            row = next(reader)

            if(len(blinkArray)>0):
                currentBlink = blinkArray[0]
            if(len(keyPressVector)>0):
                currentKeyPress = keyPressVector[0]
            all.append(row)

            #steps through the bogusFile csv to read the time and IR values and append the blinks
            for k, row in enumerate(reader):
                if(len(blinkArray)==0):
                    row.insert(4, 0)
                else:
                    rowVector = row[0].split(',')
                    if(float(row[2]) == currentBlink[0]):
                        blink = True
                        row.insert(4, row[3])
                    elif(currentBlink[1] == float(row[2])):
                        blink = False
                        row.insert(4, row[3])
                        blinkArray = blinkArray[1:]
                        if(len(blinkArray)!=0):
                            currentBlink = blinkArray[0]
                    elif(blink):
                        row.insert(4, row[3])
                    else:
                        row.insert(4, 0)
                if(len(keyPressVector)==0):
                    row.insert(5, 0)
                    all.append(row)
                #If the key press vector matches the time, and there exists a non-zero value for the blink value
                #(e.g. row(4) != 0) then we've matched a blink
                #however, we've also matched the blink if the keypress is within 100 data points of the blink
                else:
                    roundedTime = math.floor(float(row[2])*100)/100
                    roundedKeyPress = math.floor(currentKeyPress*100)/100
                    if(roundedTime >= roundedKeyPress - 0.1 and roundedTime <= roundedKeyPress + 0.1):
                        row.insert(5, row[3])
                        all.append(row)
                        keyPressVector = keyPressVector[1:]
                        if(len(keyPressVector)!=0):
                            currentKeyPress = keyPressVector[0]
                        if row[4] != 0:
                            self.MatchedBlinks = self.MatchedBlinks + 1
                    else:
                        row.insert(5, 0)
                        all.append(row)
            #writes to the new file, filename
            writer.writerows(all)

    '''
    Saves a separate file when the code is run with test = True so comparisons can be made with different files
    with different algorithm settings. Called by testMainFn.py
    Inputs:     None
    Outpus:     None
    '''
    def saveTestFile(self):
        blinkArray = self.openBlinks()
        print blinkArray
        self.DetectedBlinks = len(blinkArray)

        with open(self.filename, 'rb') as input, open((self.testFileName), 'wb') as output:
            writer = csv.writer(output, delimiter=',')
            reader = csv.reader(input, delimiter = ',')
            blink = False
            all = []
            row = next(reader)

            if(len(blinkArray)>0):
                currentBlink = blinkArray[0]
            all.append(row)
            
            for k, row in enumerate(reader):
                if(len(blinkArray)==0):
                    row[4] = 0
                else:
                    rowVector = row[0].split(',')
                    if(float(row[2]) == currentBlink[0]):
                        blink = True
                        row[4] = row[3]
                    elif(currentBlink[1] == float(row[2])):
                        blink = False
                        row[4] = row[3]
                        blinkArray = blinkArray[1:]
                        if(len(blinkArray)!=0):
                            currentBlink = blinkArray[0]
                    elif(blink):
                        row[4] = row[3]
                    else:
                        row[4] = 0
                all.append(row)

            writer.writerows(all)


    '''
    Appends new blinks to the current blink rate time period. For example, if we want to calculate the number of
    blinks in the past 5 minutes, this will add any new blinks to the subBlink vector, which includes all blinks
    in the last 5 minutes
    Inputs:     newBlink (vector including the blink to append in the form
                [blink start time in minutes, blink end time in minutes])
    Outputs:    None
    '''
    def AddBlinksInWindow(self,newBlink):
        tEnd = self.minutes
        tBegin = tEnd - self.tWindow
        self.subBlink.append(newBlink)
        firstBlink = self.subBlink[0]

        #If the first blink occured more than tWindow ago, then remove it from subBlink
        if(firstBlink[0] < tBegin):
            self.subBlink = self.subBlink[1:]

    '''
    At each time step it checks if the first blink occured more than tWindow minutes ago. If so, it removes it from
    the subBlink vector (which contains the blink rate data)
    Inputs:     None
    Outpus:     None
    '''
    def UpdateBlinksInWindow(self):
        tEnd = self.minutes
        tBegin = tEnd - self.tWindow
        if(len(self.subBlink) != 0):
            firstBlink = self.subBlink[0]
            if(firstBlink[0] < tBegin):
                self.subBlink = self.subBlink[1:]

    '''
    Reads the comma-delimited csv file and writes it to lists for the test functionality of the code. It then
    plots the lists.
    Inputs:     mode
                    1: plots the data from the indicated excel file
                    2: retrieves data needed for test mode
    Outputs:    Only outputs if in mode 2. Then it returns a vector in the form [Time, RawIR, Hour, Minute], which
                is the data from the indicated excel file
    '''
    def csv_reader(self, mode):
        if(mode == 1):
            if(test):
                inputFile = self.testFileName
            else:
                inputFile = self.filename
        else:
            inputFile = self.filename
        with open(inputFile, 'r') as csv_file:
            reader = csv.reader(csv_file, delimiter = ',')
            Hour = [];
            Minute = [];
            Time = [];
            RawIR = [];
            Blinks = [];
            ActualBlinks = [];


            # Skips the first line which does not contain data
            next(reader)

            for row in reader:
                if mode == 2:
                    Hour.append(float(row[0]))
                    Minute.append(float(row[1]))
                elif mode==1:
                    Blinks.append(float(row[4]))
                    ActualBlinks.append(float(row[5]))
                Time.append(float(row[2]))
                RawIR.append(float(row[3]))
                
            if mode ==1:
                totalOpTime = max(Time) - min(Time)
                print "Average Sampling Frequency: "
                print len(Time)/totalOpTime
                if(self.MatchedBlinks != 0 and self.ActualBlinks != 0 and self.DetectedBlinks !=0):
                    print "Accuracy of Blink Detection: " + str(self.MatchedBlinks/self.ActualBlinks)
                    print "# of Actual Blinks: " + str(self.ActualBlinks)
                    print "# of Detected Blinks: " + str(self.DetectedBlinks)
            
                pl.rcParams.update({'font.size': 18})
                pl.figure(1)
                pl.xlabel("Time(s)")
                pl.ylabel("IR Values")
                pl.title("IR Blink Sensor Results")
                pl.plot(Time, RawIR, linewidth = 2, color = 'gray')
                pl.autoscale()
                pl.plot(Time, Blinks, linewidth = 2, color = 'red')
                pl.plot(Time, ActualBlinks, linewidth = 2, color = 'blue')
                pl.show()
            else:
                return [Time, RawIR, Hour, Minute]



            

