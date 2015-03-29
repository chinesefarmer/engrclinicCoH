import csv
from serial import *
from datetime import *
import time
import pylab as pl
#from KeyPress import *

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
negative = 0
#Running average of derivatives
runningAvg = 0
error = 0;

#Any derivatives above/below these values are considered part of a blink
negSlopeThresh = -23000
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


'''BEN: This is the function that does some custom settings for the serial connection with the Arduino.
It also starts the csv file where my data will be saved. usb is defined in the main function at the bottom.
I think you should be able to merge any of your custom functions for the serial connection in with my function.'''
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

'''BEN: This is the code that read my data from the serial connection, just for your reference. I recommend using
portions of it since the blink sensor every once and sends a bogus value, and this function prevents the code from
crashing'''
def oldGetSerialCode(usb):
    buffer = usb.readline()

        
    if '\n' in buffer:
        lines = buffer.split('\n')
        IR1 = lines[-2]
        '''BEN: You only have to worry about the \r for the last variable in the serial stream from the arduino,
        so don't worry about the IR1.split('\r') if the IR data isn't the last in the vector sent to python'''
        if '\r' in IR1:
            '''BEN: Always set the IR value to the variable IR1 Bogus'''
            IR1Bogus = IR1.split('\r')
            if len(IR1Bogus) > 12:
                print "Error"
            else:
                '''BEN: This try except you definitely want to keep. It takes the IR1Bogus variable from above
                and checks if it's a valid number or not so the code doesn't crash'''
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

'''BEN: Make sure to call this function and input the newest IR1 value from the serial data. This runs the algorithm''' 
def Algorithm(IR1):
    global minutes, IRVector, tVector, blinkVector, startTime, tPrintBlink
    global negSlopeThresh, posSlopeThresh, error
    global derivVector, n, trackPos, trackNeg, startIR, startIndex, endIndex, startT
    global endT, endIR, peak, valley, blinkRange, negB, posB, positive, negative, runningAvg

                 

        timeD = datetime.now().time()
        timeDate = datetime.now().date()
        
        tDif = abs(minutes - startTime - tPrintBlink)
        if(tDif < 10**-2):
            print ""
            print "--------------------------------------------------"
            print str(len(subBlink)) + " blinks in the last " + str(round(tWindow,1)) + " minutes"
            print "--------------------------------------------------"
            print ""
            startTime = minutes

        UpdateBlinksInWindow()
                
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
                                        if(len(blinkRange)>0):
                                            AddBlinksInWindow(blinkRange[-1])
                                        if debug:
                                            print "Blink from : " + str(startT) + " minutes to "+str(endT)+" minutes"
                                        print "Length of blink: " + str(round((endT-startT)*60,2)) + " sec"
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
                                    if(len(blinkRange)>0):
                                            AddBlinksInWindow(blinkRange[-1])
                                    if debug:
                                        print "Blink from : " + str(startT) + " minutes to "+str(endT)+" minutes"
                                    print "Length of blink: " + str(round((endT-startT)*60,2)) + " sec"
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
                                        if debug:
                                            print "Blink from : " + str(startT) + " minutes to "+str(endT)+" minutes"
                                        print "Length of blink: " + str(round((endT-startT)*60,2)) + " sec"
                                        blinkVector.extend(IRVector[startIndex:i+1])
                                        if(len(blinkRange)>0):
                                            AddBlinksInWindow(blinkRange[-1])
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
                                    if debug:
                                        print "Blink from : " + str(startT) + " minutes to "+str(endT)+" minutes"
                                    print "Length of blink: " + str(round((endT-startT)*60,2)) + " sec"
                                    if(len(blinkRange)>0):
                                            AddBlinksInWindow(blinkRange[-1])
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


'''BEN: This is the code that saves my data to the csv file when you force quit the application, make sure to call this
at some point'''
def saveFile(usb):
    global minutes, IRVector, tVector, blinkVector, startTime, tPrintBlink
    global negSlopeThresh, posSlopeThresh, error
    global derivVector, n, trackPos, trackNeg, startIR, startIndex, endIndex, startT
    global endT, endIR, peak, valley, blinkRange, negB, posB, positive, negative, runningAvg
    #####Call KeyPress.py here!!!!
    keyPressVector = []
    if CheckKeyPress:
        keyPressVector = getKeyPressVector()
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
                if(tVector[k] == currentKeyPress[0]):
                    row.insert(5, IRVector[k])
                    all.append(row)
                    keyPressVector = keyPressVector[1:]
                    if(len(keyPressVector)!=0):
                        currentKeyPress = keyPressVector[0]
                else:
                    row.insert(5, 0)
                    all.append(row)

        writer.writerows(all)






if __name__=='__main__':
    filename = raw_input('Enter a file name w/ .csv at the end:  ')
    outputFile = (filename[:-4] + 'Full.csv' )
    usb = Serial('/dev/cu.usbmodem621',57600)
    initSerialConnection(usb)
    '''BEN: This is the loop I'm using right now to keep getting serial data and then save it to a usb when the user
hits ctrl-c (or keyboard interrupts the shell)'''
    while True:
        try:
            getSerial(usb)
        except KeyboardInterrupt:
            saveFile(usb)
            csv_reader(outputFile)
            break
            

