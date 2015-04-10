#removed Y:D:M from the first column of save file
#tVector needs to be cleared out occasionally
import csv
import math
from serial import *
from datetime import *
import time
import pylab as pl
from KeyPress import *
import numpy as np
#Check different base lines for smoothing algorithms?
#Yo! You're saving a duplicate of your data in your Full.csv file. Look into this...
debug = False
test = False
error = 0
#YO TEAM!!!
#You must ALWAYS type usb.close() after you keyboard interrupt the code to quit
#otherwise you'll be forced to unplug and replug the sensor




#Set port and baudRate when calling this function
def initSerialConnection(usb, BlinkSensor):
    usb.timeout = 1
    
    #This hopefully resets the Arduino
    usb.setDTR(False)
    time.sleep(1)
    usb.flushInput()
    usb.setDTR(True)
    
    buffer = ''
    BlinkSensor.saveBlinks([],1)
    if BlinkSensor.CheckKeyPress == True:
        BlinkSensor.csv_writer(["Hour","Minute","Second","IR1","Blinks", "Actual Blinks"], 1)
    else:
        BlinkSensor.csv_writer(["Hour","Minute","Second","IR1","Blinks"], 1)

def getSerial(usb, BlinkSensor):
    global error
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
                try:
                    IR1 = float(IR1Bogus[0])
                except ValueError:
                    error = 1
                    print "Value Error"
                    
        else:
            try:
                IR1 = float(IR1)
            except ValueError:
                error = 1
                print "Value Error"
                
        if(error == 1):
            print "Error"
            error = 0
        else:
            BlinkSensor.Algorithm(IR1, False)


class BlinkSensor:
    def __init__(self):
        #Any derivatives above/below these values are considered part of a blink
        self.negSlopeThresh = -6000
        self.posSlopeThresh = 13000
        self.PeakBlinkHeight = 500
        self.ValleyBlinkHeight = 1000

        self.filename = ''
        self.bogusFile = 'bogus.csv'
        self.CheckKeyPress = True
        self.IRVector = []
        self.tVector = []
        self.minVector = []
        #Vector containing blink data for the blinks in the last X seconds, where X is tWindow
        self.subBlink = []
        #Number of blinks in the last X seconds, where X is tWindow
        self.tWindow = 1.0/3
        #How often we print number of blinks in last X seconds, where X is tWindow
        self.tPrintBlink = 1.0/6
        self.minutes = 0
        timeStamp = datetime.now().time()
        #Used for keeping track of the starting time value of the subBlink vector
        self.startTime = (timeStamp.hour*60 +
                          timeStamp.minute +
                          (timeStamp.second + 0.000001*timeStamp.microsecond)/60)
        self.n=4
        self.lookForPeak = False
        self.lookForValley = False
        self.startIR = 0
        self.startIndex = 0
        self.endIndex = 0
        self.blinkStart = 0
        self.blinkStartMinutes = 0
        self.blinkEnd = 0
        self.blinkEndMinutes = 0
        self.endIR = 0
        self.peak = 0
        self.valley = 0
        self.negativeSlope = False
        self.positiveSlope = False
        self.positive = 0
        self.negative = 0
        self.ActualBlinks = 0
        self.MatchedBlinks = 0
        self.DetectedBlinks = 0
        self.timeTestMode = 0
        self.minTestMode = 0
        #To keep track of how many IR values fall are above the positive threshold.
        #if this is below n when the code comes to the end of a blink, that means it was actually a
        #false alarm.
        self.negBlinkPoints = 0

    def clearParameters(self, i):
        self.blinkEnd = 0
        self.blinkEndMinutes = 0
        self.endIndex = 0
        self.endIR = 0
        self.lookForPeak = False
        self.lookForValley = False
        self.blinkStartMinutes = 0
        self.blinkStart = 0
        self.startIR = 0
        self.peak = 0
        self.valley = 0
        self.negBlinkPoints = 0
        self.positive = 0
        self.negative = 0
        self.negativeSlope = False
        self.positiveSlope = False
        
        #Clears out all except the two most recent values
        self.IRVector = self.IRVector[i-1:]
        self.tVector = self.tVector[i-1:]
        self.minVector = self.minVector[i-1:]
        

    #When opening the csv file, remember to select the delimiter as commas
    #(open office is stupid and won't put the data in separate columns otherwise)
    #mode = 1 means overwrite the old values from the last run
    def csv_writer(self,data, mode):
        if mode == 1:
            with open(self.bogusFile, 'w') as csv_file:
                writer = csv.writer(csv_file, delimiter=',')
                writer.writerow(data)
        else:
            with open(self.bogusFile, 'a') as csv_file:
                writer = csv.writer(csv_file, delimiter=',')
                writer.writerow(data)                         

    
    def Algorithm(self,IR1,testMode):
        global debug
        global test
        if(testMode == False):
            timeD = datetime.now().time()
            self.minutes = timeD.hour*60 + timeD.minute + (timeD.second + 0.000001*timeD.microsecond)/60
            seconds = (timeD.second + 0.000001*timeD.microsecond)
            self.tVector.append(seconds)
            self.minVector.append(self.minutes)

            tDif = abs(self.minutes - self.startTime - self.tPrintBlink)
            if(tDif < 10**-2):
                print 
                print "--------------------------------------------------"
                print (str(len(self.subBlink)) + " blinks in the last " +
                       str(round(self.tWindow,1)) + " minutes")
                print "--------------------------------------------------"
                print 
                self.startTime = self.minutes

            self.UpdateBlinksInWindow()
        else:
            #########
            self.tVector.append(self.timeTestMode)
            self.minVector.append(self.minTestMode)
        #Do some blink sensing stuff
        self.IRVector.append(IR1)


        if(len(self.IRVector) > 1):
            i = len(self.IRVector)-1
            
            #Take the derivative
            deriv = (self.IRVector[i]-self.IRVector[i-1])/(self.tVector[i]-self.tVector[i-1])

            #If it's a positive slope above the threshold, start tracking
            if(self.lookForPeak):
                self.PeakAlgorithm(i, deriv)
                  
            elif(self.lookForValley):
                self.ValleyAlgorithm(i, deriv)

            #This runs the first time through since we haven't checked the
            #slopes yet
            else:
                #May be dealing with a peak
                if(deriv >= self.posSlopeThresh):
                    #start tracking the slope!
                    if debug:
                        print ("Looking for peak at time: " + str(self.tVector[i-1])
                               + "after deriv: " + str(deriv))
                    self.lookForPeak = True
                    self.blinkStart = self.tVector[i-1]
                    self.blinkStartMinutes = self.minVector[i-1]
                    self.startIndex = i-1
                    self.startIR = self.IRVector[i-1]
                    self.peak = self.IRVector[i-1]
                #May be dealing with a valley
                elif(deriv <= self.negSlopeThresh):
                    if debug:
                        print ("Looking for valley at time: " + str(self.tVector[i-1])
                               + "after deriv: " + str(deriv))
                    self.lookForValley = True
                    self.blinkStart = self.tVector[i-1]
                    self.blinkStartMinutes = self.minVector[i-1]
                    self.startIR = self.IRVector[i-1]
                    self.startIndex = i-1
                    self.valley = self.IRVector[i-1]
                else:
                    self.clearParameters(i)
        if(test == False):
            data = [str(timeD.hour),str(timeD.minute),str(timeD.second + 0.000001*timeD.microsecond),IR1]
            self.csv_writer(data, 0)

        #maybe this should return an i value? 
    def PeakAlgorithm(self,i, deriv):
        global debug
        #If the IRVal is greater than the previous peak, this is now
        #considered the peak
        if(self.IRVector[i-1] > self.peak):
            self.peak = self.IRVector[i-1]
        
        if(deriv < 0):
            #If at any point the running average is "flat", meaning the slope is
            #less than the positive threshold and greater than the negative one,
            #that likely means we're at the end of the blink
            if(deriv > self.negSlopeThresh):
                if debug:
                    print "Nearing end of peak at "+str(self.tVector[i])+" sec w/ deriv "+ str(deriv)
                self.negative = self.negative + 1
                if(self.negative > self.n):
                    self.blinkEnd = self.tVector[i-2]
                    self.blinkEndMinutes = self.minVector[i-2]
                    self.endIndex = i-2
                    self.endIR = self.IRVector[i-2]
                        #Would this be a good spot to clear out the vector?
                    if((self.peak-self.endIR) > self.PeakBlinkHeight and
                       (self.peak-self.startIR) > self.PeakBlinkHeight):
                        self.saveBlinks([[self.blinkStart, self.blinkEnd]],2)
                        self.AddBlinksInWindow([self.blinkStartMinutes, self.blinkEndMinutes])
                        if debug:
                            print "Blink from : " + str(self.blinkStart) + " sec to "+str(self.blinkEnd)+" sec"
                        print "Length of blink: " + str(round((self.blinkEnd-self.blinkStart),3)) + " sec"
                        
                    #It's not a blink unless the height is large enough, set by the BlinkHeight
                    #variable
                    else:
                        if debug:
                            print "Peak ignored at " + str(self.tVector[i]) + " sec, height not large enough"

                    self.clearParameters(i)                                                            
                else:
                    self.negativeSlope = True
            else:
                if debug:
                    print ("Switching from tracking pos to neg slope at " +str(self.tVector[i])
                           +" sec with deriv "+str(deriv))
                self.negativeSlope = True
                
        elif(self.negativeSlope):
            if debug:
                print "Inside elif(negativeSlope) the deriv is "+str(deriv)+" and positive = "+str(self.positive)
            if(self.positive == 0):
                self.positive = 1
            elif(self.positive == 1):
                self.positive = 2
            else:
                self.blinkEnd = self.tVector[i-2]
                self.blinkEndMinutes = self.minVector[i-2]
                self.endIndex = i-2
                self.endIR = self.IRVector[i-2]
                if((self.peak-self.endIR) > self.PeakBlinkHeight and (self.peak-self.startIR) > self.PeakBlinkHeight):
                    if debug:
                        print "Ending time is: " + str(self.blinkEnd)
                    self.saveBlinks([[self.blinkStart, self.blinkEnd]],2)
                    self.AddBlinksInWindow([self.blinkStartMinutes, self.blinkEndMinutes])
                    if debug:
                        print "Blink from : " + str(self.blinkStart) + " sec to "+str(self.blinkEnd)+" sec"
                    print "Length of blink: " + str(round((self.blinkEnd-self.blinkStart),2)) + " sec"
                else:
                    if debug:
                        print "Peak ignored at " + str(self.tVector[i]) + " sec, height not large enough, inside elif(negativeSlope)"

                self.clearParameters(i)


    def ValleyAlgorithm(self,i, deriv):
        global debug
        #If the IRVal is greater than the previous peak, this is now
        #considered the peak
        if(self.IRVector[i-1] < self.valley):
            self.valley = self.IRVector[i-1]
        #We're coming up from the valley
        if(deriv > 0):
            #If the derivative is less than the positive threshold, that means
            #we've likely flattened out
            if(deriv < self.posSlopeThresh):
                if debug:
                    print "Nearing end of valley at "+str(self.tVector[i])+" sec"
                self.positive = self.positive + 1
                #If there's been a positive slope for n times, the blink is over
                if(((self.positive > self.n) and (self.endIR - self.valley > self.ValleyBlinkHeight )and ((self.startIR - self.valley) > self.ValleyBlinkHeight))
                or (((self.positive > self.n + 7) and (self.endIR - self.valley) > self.ValleyBlinkHeight) and ((self.startIR - self.valley) > self.ValleyBlinkHeight))):
                    self.blinkEnd = self.tVector[i-2]
                    self.blinkEndMinutes = self.minVector[i-2]
                    self.endIndex = i-2
                    self.endIR = self.IRVector[i-2]
                    if(self.negBlinkPoints >= self.n-1):
                        if debug:
                            print "Ending time is: " + str(self.blinkEnd)
                        self.saveBlinks([[self.blinkStart, self.blinkEnd]],2)
                        if debug:
                            print "Blink from : " + str(self.blinkStart) + " sec to "+str(self.blinkEnd)+" sec"
                        print "Length of blink: " + str(round((self.blinkEnd-self.blinkStart),2)) + " sec"
                        self.AddBlinksInWindow([self.blinkStartMinutes, self.blinkEndMinutes])
                    else:
                        if debug:
                            print "Blink ignored since only "+str(self.negBlinkPoints)+" points in the negative slope. Time stamp: "+  str(self.tVector[i])

                    self.clearParameters(i)

                #Otherwise note that we have a positive slope right now
                else:
                    self.positiveSlope = True
            else:
                self.positiveSlope = True
        #If the slope is negative after we've been coming out of the valley, that
        #means the blink is over. positiveSlope just means that previoulsy there was a trend of a positive
        #slope, so if for some reason the slope is negative again, that means the blink is over.
        elif(self.positiveSlope):
            #Just in case I'll wait one round to be sure
            if(self.negative == 0):
                self.negative = 1
            elif(self.negative == 1):
                self.negative = 2
            else:
                self.blinkEnd = self.tVector[i-2]
                self.blinkEndMinutes = self.minVector[i-2]
                self.endIndex = i-2
                self.endIR = self.IRVector[i-2]
                if((self.endIR - self.valley) > self.ValleyBlinkHeight and (self.startIR - self.valley) > self.ValleyBlinkHeight):
                    if(self.negBlinkPoints >= self.n-1):
                        if debug:
                            print "Ending time is: " + str(self.blinkEnd)
                        self.saveBlinks([[self.blinkStart, self.blinkEnd]],2)
                        if debug:
                            print "Blink from : " + str(self.blinkStart) + " sec to "+str(self.blinkEnd)+" sec"
                        print "Length of blink: " + str(round((self.blinkEnd-self.blinkStart),2)) + " sec"
                        self.AddBlinksInWindow([self.blinkStartMinutes, self.blinkEndMinutes])
                    else:
                         if debug:
                             print "Blink ignored since only "+str(self.negBlinkPoints)+" points in the negative slope. Time stamp: "+  str(self.tVector[i])
                else:
                    if debug:
                        print "Valley ignored at " + str(self.tVector[i]) + " sec, height not large enough"

                self.clearParameters(i)

        else:
            self.negBlinkPoints = self.negBlinkPoints + 1



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
            
    def openBlinks(self):
        blinkTextFile = open('Blinks.txt','r')
        lines = blinkTextFile.read().split('\n')

        
        strArray = map(lambda x: x.split(', '), lines)
        #There's always a blank line at the top of the file, so let's remove that
        strArray = strArray[2:]
        blinkArray = map(lambda x: [float(x[0]), float(x[1])], strArray)
        return blinkArray
    

    def saveFile(self):
        keyPressVector = []
        if self.CheckKeyPress:
            keyPressVectorNp = np.load('KeyPress.npy')
            keyPressVector = keyPressVectorNp.tolist()
            print "Key Press Vector: " + str(keyPressVector)
        blinkArray = self.openBlinks()
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

            writer.writerows(all)


    #tWindow must be in minutes (e.g. 60 minutes instead of 1 hour)
    def AddBlinksInWindow(self,newBlink):
        tEnd = self.minutes
        tBegin = tEnd - self.tWindow
        self.subBlink.append(newBlink)
        firstBlink = self.subBlink[0]

        if(firstBlink[0] < tBegin):
            self.subBlink = self.subBlink[1:]

    def UpdateBlinksInWindow(self):
        tEnd = self.minutes
        tBegin = tEnd - self.tWindow
        if(len(self.subBlink) != 0):
            firstBlink = self.subBlink[0]
            if(firstBlink[0] < tBegin):
                self.subBlink = self.subBlink[1:]

    #Reads the comma-delimited csv file and writes it to lists.
    #Then plots the lists.
    #mode == 1 means it will plot
    #mode == 2 retrieves data needed for test mode
    def csv_reader(self, mode):
        with open(self.filename, 'r') as csv_file:
            reader = csv.reader(csv_file, delimiter = ',')
            Hour = [];
            Minute = [];
            Time = [];
            RawIR = [];
            Blinks = [];
            ActualBlinks = [];


            # Skips the first line which does not contain data
            next(reader)

                #csv file
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


"""
I want to be taking the blink vector andwrite a function that Kat can use, that takes as input a time window, and the most recent blink value
from the blink vector. It creates a subBlinkVector that is global or saved somehow, and tacks on blinks until.
It checks each time if the first blink falls outside the window. If so, it removes it from the vector. I'll just send
to Kat the number of times you've blinked in that window, so the output is just an integer.


Maybe have a function to add to the blinkWindow vector, and then at the end of each loop call another function to make sure
that the vector is up to date, and then print out the number of blinks.
    
"""




if __name__=='__main__':
    if(test):
        filename = ('2015-04-10NicoleBelowEye3.csv')
        BlinkSensor = BlinkSensor()
        BlinkSensor.filename = filename
        BlinkSensor.saveBlinks([],1)
        data = BlinkSensor.csv_reader(2)
        Hour = data[2]
        Minute = data[3]
        #Time here means seconds and microseconds
        Time = data[0]
        RawIR = data[1]
        for i in range(len(data[0])):
            BlinkSensor.minTestMode = (Hour[i]*60 + Minute[i] + Time[i]/60)
            BlinkSensor.timeTestMode = Time[i]
            BlinkSensor.Algorithm(RawIR[i],True)
        BlinkSensor.saveFile()
        BlinkSensor.csv_reader(1)
    else:
        filename = raw_input('Enter a file name:  ')
        timeDate = datetime.now().date()
        filename = (str(timeDate)+filename+'.csv')

        usb = Serial('/dev/cu.usbmodem621',57600)
        
        BlinkSensor = BlinkSensor()
        BlinkSensor.filename = filename
        
        initSerialConnection(usb,BlinkSensor)
        while True:
            try:
                getSerial(usb, BlinkSensor)
            except KeyboardInterrupt:
                BlinkSensor.saveFile()
                BlinkSensor.csv_reader(1)
                usb.close()
                break
            

