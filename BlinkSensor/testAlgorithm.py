#Need to clear out the IR vector every once and a while#Save blinks in numpy and see if you can access one value at a time instead of loading the whole numpy#to save it into the Full.csv file#Works with 2_15_Blink_Down, 2_16_Blink_RandomMovements3, 2_16_Blink_RandomMovements4#Catches 2/3 blinks for 2_16_Blink_RandomMovements5import csvimport pylab as plblinkRange = []'''How trackNeg works (similar to how trackPos works)Check to see if the slope is below negSlopeThresh    Yes: Don't do anything    No:  Is the derivative greater than 0?         Yes:  Is the derivative less than the posSlopeThresh?            Yes: Has the derivative been less than the threshold for more than n time?                 (check if the variable positive > n or not)                 Yes: This means the IR values have been relatively flat for long enough to assume                      that the blink is OVER.                 No: Set posB = true, meaning we have had a positive slope and are trying to determine                     when the blink is over.            No: Set posB = true, but in this case our slope is above the positive threshold, meaning                we are currently coming out of the valley, and haven't approached the end of the blink        No: Is posB = true, meaning that we've had a trend of positive slopes, yet right now the            derivative is negative?            Yes: Have we had a negative slope 2 times?                Yes: The blink is OVER.                No:  Increase the negative counter to record that the slope has been negative                    after a positive slope trend.            No: This means the slope is still decreasing to the bottom of the valley (aka the                beginning of the blink)                        '''    def testAlg(data):    global blinkRange    #Any derivatives above/below these values are considered part of a blink    negSlopeThresh = -6000    posSlopeThresh = 13000    #Length of running average    n=4    PeakBlinkHeight = 500    ValleyBlinkHeight = 500    trackPos = False    trackNeg = False    derivVector = []    startIR = 0    startT = 0    endT = 0    endIR = 0    peak = 0    valley = 0    blinkVector = []    negB = False    posB = False    debug = False    positive = 0    negative = 0    #To keep track of how many IR values fall are above the positive threshold.    #if this is below n when the code comes to the end of a blink, that means it was actually a    #false alarm.    posBlinkPoints = 0    negBlinkPoints = 0        tVector = data[0]    IRVector = data[1]    #print "Entering for loop"        #Begin looping through all the IR data    #We start at 1 instead of 0 to ease taking the derivative    for i in range(1, len(IRVector)):        if i==1:            print IRVector[0]        #Take the derivative        deriv = (IRVector[i]-IRVector[i-1])/(tVector[i]-tVector[i-1])        derivVector.append(deriv)        #If it's a positive slope above the threshold, start tracking        if(trackPos):            #If the IRVal is greater than the previous peak, this is now            #considered the peak            if(IRVector[i-1] > peak):                peak = IRVector[i-1]                        if(deriv < 0):                #If at any point the running average is "flat", meaning the slope is                #less than the positive threshold and greater than the negative one,                #that likely means we're at the end of the blink                if(deriv > negSlopeThresh):                    if debug:                        print "Nearing end of peak at "+str(tVector[i])+" sec w/ deriv "+ str(deriv)                    negative = negative + 1                    if(negative > n):                        endT = tVector[i-2]                        endIndex = i-2                        endIR = IRVector[i-2]                        if(endIR == peak):                            blinkVector.extend([0]*(i-startIndex+1))                            if debug:                                print "Bad"                        elif((peak-endIR) > PeakBlinkHeight and (peak-startIR) > PeakBlinkHeight):                            ##if(posBlinkPoints >= n-2):                            blinkRange.append([startT, endT])                            blinkVector.extend(IRVector[startIndex:i+1])                                ##if(len(blinkRange)>0):                                    ##AddBlinksInWindow(blinkRange[-1])                            if debug:                                print "Blink from : " + str(startT) + " sec to "+str(endT)+" sec"                            print "Length of blink: " + str(round((endT-startT),3)) + " sec"                            #else:#                                blinkVector.extend([0]*(i-startIndex+1))#                                if debug:#                                    print "Blink ignored since only "+str(posBlinkPoints)+" points in the positive slope. Time stamp: "+  str(tVector[i])                        #It's not a blink unless the height is large enough, set by the BlinkHeight                        #variable                        else:                            blinkVector.extend([0]*(i-startIndex+1))                            if debug:                                print "Peak ignored at " + str(tVector[i]) + " sec, height not large enough"                                                                                      endT = 0                        endIndex = 0                        endIR = 0                        trackPos = False                        runningAvg = 0                        startT = 0                        startIR = 0                        peak = 0                        posBlinkPoints = 0                        #Clearing out the vector a little                        derivVector = derivVector[i-(n-1):i+1]                        positive = 0                        negative = 0                        negB = False                    else:                        negB = True                else:                    if debug:                        print "Switching from tracking pos to neg slope at " +str(tVector[i]) +" sec with deriv "+str(deriv)                    negB = True                                elif(negB):                if debug:                    print "Inside elif(negB) the deriv is "+str(deriv)+" and positive = "+str(positive)                if(positive == 0):                    positive = 1                elif(positive == 1):                    positive = 2                else:                    endT = tVector[i-2]                    endIndex = i-2                    endIR = IRVector[i-2]                    if(endIR == peak):                        blinkVector.extend([0]*(i-startIndex+1))                    elif((peak-endIR) > PeakBlinkHeight and (peak-startIR) > PeakBlinkHeight):                        ##if(posBlinkPoints >= n-2):                        if debug:                            print "Ending time is: " + str(endT)                        blinkRange.append([startT, endT])                        blinkVector.extend(IRVector[startIndex:i+1])                            ##if(len(blinkRange)>0):                                    ##AddBlinksInWindow(blinkRange[-1])                        if debug:                            print "Blink from : " + str(startT) + " sec to "+str(endT)+" sec"                        print "Length of blink: " + str(round((endT-startT),2)) + " sec"                        #else:#                            blinkVector.extend([0]*(i-startIndex+1))#                            if debug:#                                print "Blink ignored since only "+str(posBlinkPoints)+" points in the positive slope. Time stamp: "+  str(tVector[i])                    else:                        blinkVector.extend([0]*(i-startIndex+1))                        if debug:                            print "Peak ignored at " + str(tVector[i]) + " sec, height not large enough, inside elif(negB)"                    endT = 0                    endIndex = 0                    endIR = 0                    trackPos = False                    runningAvg = 0                    startT = 0                    negative = 0                    peak = 0                    posBlinkPoints = 0                    #Clearing out the vector a little                    derivVector = derivVector[i-(n-1):i+1]                    negB = False                    positive = 0            else:                posBlinkPoints = posBlinkPoints + 1                       elif(trackNeg):            #If the IRVal is greater than the previous peak, this is now            #considered the peak            if(IRVector[i-1] < valley):                valley = IRVector[i-1]            #We're coming up from the valley            if(deriv > 0):                #If the derivative is less than the positive threshold, that means                #we've likely flattened out                if(deriv < posSlopeThresh):                    if debug:                        print "Nearing end of valley at "+str(tVector[i])+" sec"                    positive = positive + 1                    #If there's been a positive slope for n times, the blink is over                    if(((positive > n) and (endIR - valley > ValleyBlinkHeight )and ((startIR - valley) > ValleyBlinkHeight))                    or (((positive > n + 7) and (endIR - valley) > ValleyBlinkHeight) and ((startIR - valley) > ValleyBlinkHeight))):                        endT = tVector[i-2]                        endIndex = i-2                        endIR = IRVector[i-2]                        if(endIR == valley):                            blinkVector.extend([0]*(i-startIndex+1))                        if(negBlinkPoints >= n-1):                            if debug:                                print "Ending time is: " + str(endT)                            blinkRange.append([startT, endT])                            if debug:                                print "Blink from : " + str(startT) + " sec to "+str(endT)+" sec"                            print "Length of blink: " + str(round((endT-startT),2)) + " sec"                            blinkVector.extend(IRVector[startIndex:i+1])                            ##if(len(blinkRange)>0):                                ##AddBlinksInWindow(blinkRange[-1])                        else:                            blinkVector.extend([0]*(i-startIndex+1))                            if debug:                                print "Blink ignored since only "+str(negBlinkPoints)+" points in the negative slope. Time stamp: "+  str(tVector[i])                                    #else:#                        blinkVector.extend([0]*(i-startIndex+1))#                        if debug:#                            print "Valley ignored at " + str(tVector[i]) + " sec, height not large enough"                                            trackNeg = False                        runningAvg = 0                        startT = 0                        endT = 0                        endIndex = 0                        endIR = 0                        valley = 0                        negBlinkPoints = 0                        positive = 0                        #Clearing out the vector a little                        derivVector = derivVector[i-(n-1):i+1]                        posB = False                        negative = 0                    #Otherwise note that we have a positive slope right now                    else:                        posB = True                else:                    posB = True            #If the slope is negative after we've been coming out of the valley, that            #means the blink is over. posB just means that previoulsy there was a trend of a positive            #slope, so if for some reason the slope is negative again, that means the blink is over.            elif(posB):                #Just in case I'll wait one round to be sure                if(negative == 0):                    negative = 1                elif(negative == 1):                    negative = 2                else:                    endT = tVector[i-2]                    endIndex = i-2                    endIR = IRVector[i-2]                    if(endIR == valley):                        blinkVector.extend([0]*(i-startIndex+1))                    elif((endIR - valley) > ValleyBlinkHeight and (startIR - valley) > ValleyBlinkHeight):                        if(negBlinkPoints >= n-1):                            if debug:                                print "Ending time is: " + str(endT)                            blinkRange.append([startT, endT])                            blinkVector.extend(IRVector[startIndex:i+1])                            if debug:                                print "Blink from : " + str(startT) + " sec to "+str(endT)+" sec"                            print "Length of blink: " + str(round((endT-startT),2)) + " sec"                            ##if(len(blinkRange)>0):                                    ##AddBlinksInWindow(blinkRange[-1])                        else:                             blinkVector.extend([0]*(i-startIndex+1))                             if debug:                                 print "Blink ignored since only "+str(negBlinkPoints)+" points in the negative slope. Time stamp: "+  str(tVector[i])                    else:                        blinkVector.extend([0]*(i-startIndex+1))                        if debug:                            print "Valley ignored at " + str(tVector[i]) + " sec, height not large enough"                    trackNeg = False                    runningAvg = 0                    startT = 0                    valley = 0                    endT = 0                    negBlinkPoints = 0                    endIndex = 0                    endIR = 0                    positive = 0                    #Clearing out the vector a little                    derivVector = derivVector[i-(n-1):i+1]                    posB = False                    negative = 0            else:                negBlinkPoints = negBlinkPoints + 1        #This runs the first time through since we haven't checked the        #slopes yet        else:            #May be dealing with a peak            if(deriv >= posSlopeThresh):                #start tracking the slope!                if debug:                    print "Looking for peak at time: " + str(tVector[i-1]) + "after deriv: " + str(deriv)                trackPos = True                startT = tVector[i-1]                startIndex = i-1                startIR = IRVector[i-1]                peak = IRVector[i-1]            #May be dealing with a valley            elif(deriv <= negSlopeThresh):                if debug:                    print "Looking for valley at time: " + str(tVector[i-1]) + "after deriv: " + str(deriv)                trackNeg = True                startT = tVector[i-1]                startIR = IRVector[i-1]                startIndex = i-1                valley = IRVector[i-1]            else:                startT = 0                startIndex = 0                startIR = 0                peak = 0                valley = 0                blinkVector.append(0)    return blinkRange'''mode = 1 is plotting mode   mode = 2 is for outputting the time vector and IR vector for the algorithm'''def csv_reader(filename, mode):    with open(filename, 'r') as csv_file:        reader = csv.reader(csv_file, delimiter = ',')        global blinkRange        MatchedBlinks = 0        Time = [];        RawIR = [];        Blinks = [];        ActualBlinks = [];        NewAlg = []        blink = False        if(mode == 1 and len(blinkRange)>0):            CurrentBlink = blinkRange[0]        # Skips the first line which does not contain data        next(reader)        i = 0            #csv file        for row in reader:            #print row            i = i+1            Time.append(float(row[2]))            RawIR.append(float(row[3]))            if(mode == 1):                Blinks.append(float(row[4]))                ActualBlinks.append(float(row[5]))                if(RawIR[-1] == ActualBlinks[-1]):                    MatchedBlinks = MatchedBlinks + 1                if(len(blinkRange)==0):                    NewAlg.append(0)                else:                    if(float(row[2]) == float(CurrentBlink[0])):                        blink = True                        NewAlg.append(float(row[3]))                    elif(float(row[2]) == CurrentBlink[1]):                        blink = False                        NewAlg.append(float(row[3]))                        blinkRange = blinkRange[1:]                        if(len(blinkRange) != 0):                            CurrentBlink = blinkRange[0]                    elif(blink):                        NewAlg.append(float(row[3]))                    else:                        NewAlg.append(0)        #When you fix the duplication error, don't do /2!!!        TotalBlinks = sum(x>0 for x in ActualBlinks)/2        MatchedBlinks = MatchedBlinks/2        print "Total Blinks: " + str(TotalBlinks)        print "Algorithm matched " + str(MatchedBlinks) + " blinks"        totalOpTime = max(Time) - min(Time)        if(mode==1):            print "Average Sampling Frequency: "            print len(Time)/totalOpTime            plot_data(Time, RawIR, Blinks, ActualBlinks, NewAlg)        elif(mode==2):            return [Time, RawIR]                    def plot_data(Time, RawIR, Blinks, ActualBlinks, NewAlg):                                             pl.rcParams.update({'font.size': 18})        pl.figure(1)        pl.xlabel("Time(s)")        pl.ylabel("IR Values")        pl.title("IR Blink Sensor Results")        pl.plot(Time, RawIR, linewidth = 2, color = 'gray')        pl.autoscale()        pl.ylim([min(RawIR)-1000, max(RawIR)+1000])        pl.plot(Time, Blinks, linewidth = 2, color = 'red')        pl.plot(Time, ActualBlinks, linewidth = 2, color = 'blue')        pl.plot(Time, NewAlg, linewidth = 2, color = 'green')        pl.show()if __name__ == "__main__":    data = csv_reader('4_3_Cindy3.csv', 2)    blinks = testAlg(data)    print blinks    csv_reader('4_3_Cindy3Full.csv', 1)