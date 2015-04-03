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
CheckKeyPress = True
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
startTime = timeStamp.hour*60 + timeStamp.minute + (timeStamp.second + 0.000001*timeStamp.microsecond)/60

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
PeakBlinkHeight = 500
ValleyBlinkHeight = 1000
negative = 0
#To keep track of how many IR values fall are above the positive threshold.
#if this is below n when the code comes to the end of a blink, that means it was actually a
#false alarm.
posBlinkPoints = 0
negBlinkPoints = 0
error = 0;

#Any derivatives above/below these values are considered part of a blink
negSlopeThresh = -6000
posSlopeThresh = 13000

#YO TEAM!!!
#You must ALWAYS type usb.close() after you keyboard interrupt the code to quit
#otherwise you'll be forced to unplug and replug the sensor


#When opening the csv file, remember to select the delimiter as commas
#(open office is stupid and won't put the data in separate columns otherwise)
def csv_writer(data):
    with open(filename, 'a') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        writer.writerow(data)


#Set port and baudRate when calling this function
def initSerialConnection(usb):
    usb.timeout = 1
    
    #This hopefully resets the Arduino
    usb.setDTR(False)
    time.sleep(1)
    usb.flushInput()
    usb.setDTR(True)
    
    buffer = ''
    csv_writer(["Y:D:M", "H:M:S", "Seconds","IR1"])

def getSerial(usb):
    global minutes, IRVector, tVector, blinkVector, startTime, tPrintBlink, blinkHeight
    global negSlopeThresh, posSlopeThresh, error, posBlinkPoints, negBlinkPoints
    global derivVector, n, trackPos, trackNeg, startIR, startIndex, endIndex, startT
    global endT, endIR, peak, valley, blinkRange, negB, posB, positive, negative

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
                 

        timeD = datetime.now().time()
        timeDate = datetime.now().date()
        
        tDif = abs(minutes - startTime - tPrintBlink)
        if(tDif < 10**-2):
            print 
            print "--------------------------------------------------"
            print str(len(subBlink)) + " blinks in the last " + str(round(tWindow,1)) + " minutes"
            print "--------------------------------------------------"
            print 
            startTime = minutes

        UpdateBlinksInWindow()
                
        if(error == 1):
            error = 0
        else:
            #Do some blink sensing stuff
            IRVector.append(IR1)
            minutes = timeD.hour*60 + timeD.minute + (timeD.second + 0.000001*timeD.microsecond)/60
            sseconds = (timeD.second + 0.000001*timeD.microsecond)
            tVector.append(sseconds)
            if(len(IRVector) > 1):
                i = len(IRVector)-1
                
                #Take the derivative
                deriv = (IRVector[i]-IRVector[i-1])/(tVector[i]-tVector[i-1])
                derivVector.append(deriv)

                #If it's a positive slope above the threshold, start tracking
                if(trackPos):
                    #If the IRVal is greater than the previous peak, this is now
                    #considered the peak
                    if(IRVector[i-1] > peak):
                        peak = IRVector[i-1]
                    
                    if(deriv < 0):
                        #If at any point the running average is "flat", meaning the slope is
                        #less than the positive threshold and greater than the negative one,
                        #that likely means we're at the end of the blink
                        if(deriv > negSlopeThresh):
                            if debug:
                                print "Nearing end of peak at "+str(tVector[i])+" sec w/ deriv "+ str(deriv)
                            negative = negative + 1
                            if(negative > n):
                                endT = tVector[i-2]
                                endIndex = i-2
                                endIR = IRVector[i-2]
                                if(endIR == peak):
                                    blinkVector.extend([0]*(i-startIndex+1))
                                    if debug:
                                        print "Bad"
                                elif((peak-endIR) > PeakBlinkHeight and (peak-startIR) > PeakBlinkHeight):
                                    if(posBlinkPoints >= n-1):
                                        blinkRange.append([startT, endT])
                                        blinkVector.extend(IRVector[startIndex:i+1])
                                        ##if(len(blinkRange)>0):
                                            ##AddBlinksInWindow(blinkRange[-1])
                                        if debug:
                                            print "Blink from : " + str(startT) + " sec to "+str(endT)+" sec"
                                        print "Length of blink: " + str(round((endT-startT),3)) + " sec"
                                    else:
                                        blinkVector.extend([0]*(i-startIndex+1))
                                        if debug:
                                            print "Blink ignored since only "+str(posBlinkPoints)+" points in the positive slope. Time stamp: "+  str(tVector[i])

                                #It's not a blink unless the height is large enough, set by the BlinkHeight
                                #variable
                                else:
                                    blinkVector.extend([0]*(i-startIndex+1))
                                    if debug:
                                        print "Peak ignored at " + str(tVector[i]) + " sec, height not large enough"
                                                                      
                                endT = 0
                                endIndex = 0
                                endIR = 0
                                trackPos = False
                                runningAvg = 0
                                startT = 0
                                startIR = 0
                                peak = 0
                                posBlinkPoints = 0
                                #Clearing out the vector a little
                                derivVector = derivVector[i-(n-1):i+1]
                                positive = 0
                                negative = 0
                                negB = False
                            else:
                                negB = True
                        else:
                            if debug:
                                print "Switching from tracking pos to neg slope at " +str(tVector[i]) +" sec"
                            negB = True
                            
                    elif(negB):
                        if debug:
                            print "Inside elif(negB) the deriv is "+str(deriv)+" and positive = "+str(positive)
                        if(positive == 0):
                            positive = 1
                        elif(positive == 1):
                            positive = 2
                        else:
                            endT = tVector[i-2]
                            endIndex = i-2
                            endIR = IRVector[i-2]
                            if(endIR == peak):
                                blinkVector.extend([0]*(i-startIndex+1))
                            elif((peak-endIR) > PeakBlinkHeight and (peak-startIR) > PeakBlinkHeight):
                                if(posBlinkPoints >= n-1):
                                    if debug:
                                        print "Ending time is: " + str(endT)
                                    blinkRange.append([startT, endT])
                                    blinkVector.extend(IRVector[startIndex:i+1])
                                    ##if(len(blinkRange)>0):
                                            ##AddBlinksInWindow(blinkRange[-1])
                                    if debug:
                                        print "Blink from : " + str(startT) + " sec to "+str(endT)+" sec"
                                    print "Length of blink: " + str(round((endT-startT),2)) + " sec"
                                else:
                                    blinkVector.extend([0]*(i-startIndex+1))
                                    if debug:
                                        print "Blink ignored since only "+str(posBlinkPoints)+" points in the positive slope. Time stamp: "+  str(tVector[i])
                            else:
                                blinkVector.extend([0]*(i-startIndex+1))
                                if debug:
                                    print "Peak ignored at " + str(tVector[i]) + " sec, height not large enough, inside elif(negB)"

                            endT = 0
                            endIndex = 0
                            endIR = 0
                            trackPos = False
                            runningAvg = 0
                            startT = 0
                            negative = 0
                            peak = 0
                            posBlinkPoints = 0
                            #Clearing out the vector a little
                            derivVector = derivVector[i-(n-1):i+1]
                            negB = False
                            positive = 0
                    else:
                        posBlinkPoints = posBlinkPoints + 1

                #This runs the first time through since we haven't checked the
                #slopes yet
                else:
                    #May be dealing with a peak
                    if(deriv >= posSlopeThresh):
                        #start tracking the slope!
                        if debug:
                            print "Looking for peak at time: " + str(tVector[i-1]) + "after deriv: " + str(deriv)
                        trackPos = True
                        startT = tVector[i-1]
                        startIndex = i-1
                        startIR = IRVector[i-1]
                        peak = IRVector[i-1]
                    #May be dealing with a valley
                    elif(deriv <= negSlopeThresh):
                        if debug:
                            print "Looking for valley at time: " + str(tVector[i-1]) + "after deriv: " + str(deriv)
                        trackNeg = True
                        startT = tVector[i-1]
                        startIR = IRVector[i-1]
                        startIndex = i-1
                        valley = IRVector[i-1]
                    else:
                        startT = 0
                        startIndex = 0
                        startIR = 0
                        peak = 0
                        valley = 0
                        blinkVector.append(0)

            data = ["%s:%s:%s" %(timeDate.year, timeDate.day, timeDate.month),
                    "%s:%s:%s" % (timeD.hour,timeD.minute,(timeD.second + 0.000001*timeD.microsecond)),
                    (timeD.second + 0.000001*timeD.microsecond) ,IR1]
            csv_writer(data)


    #change from 0 to blank
def saveFile(usb):
    global minutes, IRVector, tVector, blinkVector, startTime, tPrintBlink, CheckKeyPress
    global negSlopeThresh, posSlopeThresh, error
    global derivVector, n, trackPos, trackNeg, startIR, startIndex, endIndex, startT
    global endT, endIR, peak, valley, blinkRange, negB, posB, positive, negative, runningAvg
    #####Call KeyPress.py here!!!!
    print blinkRange
    keyPressVector = []
    if CheckKeyPress:
        print "Entering Check Key Press"
        keyPressVectorNp = np.load('KeyPress.npy')
        keyPressVector = keyPressVectorNp.tolist()
        print keyPressVector
        
    usb.close()
    blinkVector.append(0)
    blinkVector = blinkVector[0:len(IRVector)]
    with open(filename, 'rb') as input, open((filename[:-4] + 'Full.csv' ), 'wb') as output:
        reader = csv.reader(input, delimiter = ',')
        writer = csv.writer(output, delimiter = ',')
        blink = False
        all = []
        row = next(reader)
        row.insert(4, 'Blink')
        all.append(row)
        if(len(blinkRange)>0):
            currentBlink = blinkRange[0]
        if(len(keyPressVector)>0):
            currentKeyPress = keyPressVector[0]
        for k, row in enumerate(reader):
            if(len(blinkRange)==0):
                row.insert(4, 0)
                all.append(row)
            else:
                rowVector = row[0].split(',')
                if(tVector[k] == currentBlink[0]):
                    blink = True
                    row.insert(4, IRVector[k])
                    all.append(row)
                elif(currentBlink[1] == tVector[k]):
                    blink = False
                    row.insert(4, IRVector[k])
                    all.append(row)
                    blinkRange = blinkRange[1:]
                    if(len(blinkRange)!=0):
                        currentBlink = blinkRange[0]
                elif(blink):
                    row.insert(4, IRVector[k])
                    all.append(row)
                else:
                    row.insert(4, 0)
                    all.append(row)
            if(len(keyPressVector)==0):
                row.insert(5, 0)
                all.append(row)
            else:
                roundedTime = math.floor(tVector[k]*100)/100
                roundedKeyPress = math.floor(currentKeyPress*100)/100
                if(roundedTime >= roundedKeyPress - 0.1 and roundedTime <= roundedKeyPress + 0.1):
                    row.insert(5, IRVector[k])
                    all.append(row)
                    keyPressVector = keyPressVector[1:]
                    if(len(keyPressVector)!=0):
                        currentKeyPress = keyPressVector[0]
                else:
                    row.insert(5, 0)
                    all.append(row)

        writer.writerows(all)

#tWindow must be in minutes (e.g. 60 minutes instead of 1 hour)
def AddBlinksInWindow(newBlink):
    global tWindow
    global subBlink
    tEnd = minutes
    tBegin = tEnd - tWindow

    if(len(subBlink)==0 or newBlink != subBlink[-1]):
       subBlink.append(newBlink)
    firstBlink = subBlink[0]

    if(firstBlink[0] < tBegin):
        subBlink = subBlink[1:]
    #return len(subBlink)

def UpdateBlinksInWindow():
    global tWindow
    global subBlink
    tEnd = minutes
    tBegin = tEnd - tWindow
    if(len(subBlink) != 0):
        firstBlink = subBlink[0]
        if(firstBlink[0] < tBegin):
            subBlink = subBlink[1:]

#Reads the comma-delimited csv file and writes it to lists.
#Then plots the lists.
def csv_reader(filename):
    with open(filename, 'r') as csv_file:
        reader = csv.reader(csv_file, delimiter = ',')

        Time = [];
        RawIR = [];
        Blinks = [];
        ActualBlinks = [];


        # Skips the first line which does not contain data
        next(reader)

            #csv file
        for row in reader:
            #print row
            Time.append(float(row[2]))
            RawIR.append(float(row[3]))
            Blinks.append(float(row[4]))
            ActualBlinks.append(float(row[5]))
            

        totalOpTime = max(Time) - min(Time)
        print "Average Sampling Frequency: "
        print len(Time)/totalOpTime
            
        
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


"""
I want to be taking the blink vector andwrite a function that Kat can use, that takes as input a time window, and the most recent blink value
from the blink vector. It creates a subBlinkVector that is global or saved somehow, and tacks on blinks until.
It checks each time if the first blink falls outside the window. If so, it removes it from the vector. I'll just send
to Kat the number of times you've blinked in that window, so the output is just an integer.


Maybe have a function to add to the blinkWindow vector, and then at the end of each loop call another function to make sure
that the vector is up to date, and then print out the number of blinks.
    
"""




if __name__=='__main__':
    filename = raw_input('Enter a file name w/ .csv at the end:  ')
    outputFile = (filename[:-4] + 'Full.csv' )
    usb = Serial('/dev/cu.usbmodem621',57600)
    initSerialConnection(usb)
    while True:
        try:
            getSerial(usb)
        except KeyboardInterrupt:
            saveFile(usb)
            csv_reader(outputFile)
            break
            

