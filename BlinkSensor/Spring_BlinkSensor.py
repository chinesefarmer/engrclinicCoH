import csv
from serial import *
from datetime import *
import time

IRVector = []
tVector = []
derivVector = []
blinkVector = []
subBlink = []
debug = False

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
def receiving(usb):
    error = 0;
    usb.timeout = 1
    global IRVector
    global tVector
    global blinkVector
    #Any derivatives above/below these values are considered part of a blink
    negSlopeThresh = -23000
    posSlopeThresh = 13000
    global derivVector
    #Length of running average
    n=4
    dummy = 0
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
    
    #This hopefully resets the Arduino
    usb.setDTR(False)
    time.sleep(1)
    usb.flushInput()
    usb.setDTR(True)
    
    buffer = ''
    csv_writer(["Y:D:M", "H:M:S", "Seconds","IR1"])

    try:
        while True:
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
                if(error == 1):
                    error = 0
                else:
                    #Do some blink sensing stuff
                    IRVector.append(IR1)
                    minutes = timeD.hour*60 + timeD.minute + (timeD.second + 0.000001*timeD.microsecond)/60
                    tVector.append(minutes)
                    if(len(IRVector) > 1):
                        i = len(IRVector)-1
                        
                        #Take the derivative
                        deriv = (IRVector[i]-IRVector[i-1])/(tVector[i]-tVector[i-1])
                        derivVector.append(deriv)
                        
                        if(trackPos):
                            if debug:
                                print "Tracking positive slope"
                            if(len(derivVector)<n):
                                runningAvg = sum(derivVector)/len(derivVector)
                            else:
                                runningAvg = sum(derivVector[i-(n-1):i+1])/n
                            
                            #This means it was a false alarm, I may need two positive thresholds
                            #I'm saying this isn't a blink if the running average falls below a threshold
                            #and the slope hasn't been within the threshold for n or more values
                            if(runningAvg < posSlopeThresh and len(derivVector) < n):
                                blinkVector.extend([0]*(i-startIndex))
                                if debug:
                                    print "False Positive Alarm w/ Deriv: " + str(deriv)
                                    print "Time = " + str(time[i])
                                trackPos = False
                                runningAvg = 0
                                startT = 0
                                startIndex = 0
                                startIR = 0
                                peak = 0
                            #Otherwise we might be part of the slope still
                            else:
                                #If the IRVal is greater than the previous peak, this is now
                                #considered the peak
                                if(IRVector[i-1] > peak):
                                    peak = IRVector[i-1]
                                #If at any point the running average is "flat", meaning the slope is
                                #less than the positive threshold and greater than the negative one,
                                #that likely means we're at the end of the blink
                                if(deriv < 0):
                                    if(deriv > negSlopeThresh):
                                        negative = negative + 1
                                        if(negative > n):
                                            endT = tVector[i-2]
                                            endIndex = i-2
                                            endIR = IRVector[i-2]
                                            if(endIR == peak):
                                                blinkVector.extend([0]*(i-startIndex+1))
                                                if debug:
                                                    print "Bad"
                                            elif((peak-endIR) > 1000 and (peak-startIR) > 1000):
                                                if debug:
                                                    print "Ending time is: " + str(endT)
                                                    print "Ending deriv is " + str(deriv)
                                                blinkRange.append([startT, endT])
                                                blinkVector.extend(IRVector[startIndex:i+1])
                                                print "Blink from : " + str(startT) + " minutes to "+str(endT)+" minutes"
                                            else:
                                                blinkVector.extend([0]*(i-startIndex+1))
                                                 
                                            endT = 0
                                            endIndex = 0
                                            endIR = 0
                                            trackPos = False
                                            runningAvg = 0
                                            startT = 0
                                            startIR = 0
                                            peak = 0
                                            #Clearing out the vector a little
                                            derivVector = derivVector[i-(n-1):i+1]
                                            positive = 0
                                            negative = 0
                                            negB = False
                                        else:
                                            negB = True
                                    else:
                                        negB = True
                                        
                                elif(negB):
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
                                        elif((peak-endIR) > 1000 and (peak-startIR) > 1000):
                                            if debug:
                                                print "Ending time is: " + str(endT)
                                            blinkRange.append([startT, endT])
                                            blinkVector.extend(IRVector[startIndex:i+1])
                                            print "Blink from : " + str(startT) + " minutes to "+str(endT)+" minutes"
                                        else:
                                            blinkVector.extend([0]*(i-startIndex+1))
                                        endT = 0
                                        endIndex = 0
                                        endIR = 0
                                        trackPos = False
                                        runningAvg = 0
                                        startT = 0
                                        peak = 0
                                        #Clearing out the vector a little
                                        derivVector = derivVector[i-(n-1):i+1]
                                        negB = False
                                        positive = 0
                                
                        elif(trackNeg):
                            if debug:
                                print "Tracking negative slope w/ deriv: " + str(deriv)
                            if(len(derivVector)<n):
                                runningAvg = sum(derivVector)/len(derivVector)
                            else:
                                runningAvg = sum(derivVector[i-(n-1):i+1])/n
                            if debug:    
                                print "Running Average: " + str(runningAvg)
                            
                            #This means it was a false alarm, I may need two positive thresholds
                            #I'm saying this isn't a blink if the running average falls below a threshold
                            #and the slope hasn't been within the threshold for n or more values
                            if(runningAvg > negSlopeThresh and len(derivVector) < n):
                                if debug:
                                    print "False Negative Alarm w/ Deriv: " + str(deriv)
                                    print "Time = " + str(time[i])
                                trackNeg = False
                                runningAvg = 0
                                startT = 0
                                startIndex = 0
                                startIR = 0
                                valley = 0
                            #Otherwise we might be part of the slope still
                            else:
                                #If the IRVal is greater than the previous peak, this is now
                                #considered the peak
                                if(IRVector[i-1] < valley):
                                    valley = IRVector[i-1]
                                #We're coming up from the valley
                                if(deriv > 0):
                                    #If the derivative is less than the positive threshold, that means
                                    #we've likely flattened out
                                    if(deriv < posSlopeThresh):
                                        positive = positive + 1
                                        #If there's been a positive slope for n times, the blink is over
                                        if(positive > n):
                                            endT = tVector[i-2]
                                            endIndex = i-2
                                            endIR = IRVector[i-2]
                                            if(endIR == valley):
                                                blinkVector.extend([0]*(i-startIndex+1))
                                            elif((endIR - valley) > 1000 and (startIR - valley) > 1000):
                                                if debug:
                                                    print "Ending time is: " + str(endT)
                                                blinkRange.append([startT, endT])
                                                print "Blink from : " + str(startT) + " minutes to "+str(endT)+" minutes"
                                                blinkVector.extend(IRVector[startIndex:i+1])
                                            else:
                                                blinkVector.extend([0]*(i-startIndex+1))
                                            trackNeg = False
                                            runningAvg = 0
                                            startT = 0
                                            endT = 0
                                            endIndex = 0
                                            endIR = 0
                                            valley = 0
                                            positive = 0
                                            #Clearing out the vector a little
                                            derivVector = derivVector[i-(n-1):i+1]
                                            posB = False
                                            negative = 0
                                        #Otherwise note that we have a positive slope right now
                                        else:
                                            posB = True
                                    else:
                                        posB = True
                                #If the slope is negtaive after we've been coming out of the valley, that
                                #means the blink is over
                                elif(posB):
                                    #Just in case I'll wait one round to be sure
                                    if(negative == 0):
                                        negative = 1
                                    elif(negative == 1):
                                        negative = 2
                                    else:
                                        endT = tVector[i-2]
                                        endIndex = i-2
                                        endIR = IRVector[i-2]
                                        if(endIR == valley):
                                            blinkVector.extend([0]*(i-startIndex+1))
                                        elif((endIR - valley) > 1000 and (startIR - valley) > 1000):
                                            if debug:
                                                print "Ending time is: " + str(endT)
                                            blinkRange.append([startT, endT])
                                            blinkVector.extend(IRVector[startIndex:i+1])
                                            print "Blink from : " + str(startT) + " minutes to "+str(endT)+" minutes"
                                        else:
                                            blinkVector.extend([0]*(i-startIndex+1))
                                        trackNeg = False
                                        runningAvg = 0
                                        startT = 0
                                        valley = 0
                                        endT = 0
                                        endIndex = 0
                                        endIR = 0
                                        #Clearing out the vector a little
                                        derivVector = derivVector[i-(n-1):i+1]
                                        posB = False
                                        negative = 0

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
                    #may not work....
                    if(len(blinkRange)>0):
                        BlinksInWindow(0.5,blinkRange[-1])
    
    #change from 0 to blank
    except KeyboardInterrupt:
        usb.close()
        print blinkRange
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
            currentBlink = blinkRange[0]
            for k, row in enumerate(reader):
                if(len(blinkRange)==0):
                    row.insert(4, '')
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
                        row.insert(4, '')
                        all.append(row)

            writer.writerows(all)

#tWindow must be in minutes (e.g. 60 minutes instead of 1 hour)
def BlinksInWindow(tWindow, newBlink):
    global subBlink
    timeD = datetime.now().time()
    tEnd = timeD.hour*60 + timeD.minute + (timeD.second + 0.000001*timeD.microsecond)/60
    tBegin = tEnd - tWindow

    if(len(subBlink)==0 or newBlink != subBlink[-1]):
       subBlink.append(newBlink)
    firstBlink = subBlink[0]

    if(firstBlink[0] < tBegin):
        subBlink = subBlink[1:]
    print "You have blinked " + str(len(subBlink))+" times in the last "+str(tWindow)+" minutes"
    return len(subBlink)
    

if __name__=='__main__':
    filename = raw_input('Enter a file name w/ .csv at the end:  ')
    usb = Serial('/dev/cu.usbmodem621',57600)
    receiving(usb)

"""
I want to be taking the blink vector andwrite a function that Kat can use, that takes as input a time window, and the most recent blink value
from the blink vector. It creates a subBlinkVector that is global or saved somehow, and tacks on blinks until.
It checks each time if the first blink falls outside the window. If so, it removes it from the vector. I'll just send
to Kat the number of times you've blinked in that window, so the output is just an integer.

    
"""
