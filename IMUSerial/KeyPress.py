import csv
from serial import *
from datetime import *
import time
import pylab as pl
import numpy as np

keyPressVector = []

'''
User presses enter every time the subject blinks. The time stamp of this key press is saved in
a .npy file which is later read by Spring_BlinkSensor.py and appended to the file containing all
the blink sensor data
Inputs:     None
Outputs:    None
'''
def KeyPress():
    blink = ''
    while True:
        try:
            blink = raw_input("Press enter if you blink.                    ")
            timeD = datetime.now().time()
            minutes = (timeD.hour*60 + timeD.minute +
                    (timeD.second + 0.000001*timeD.microsecond)/60)
            seconds = (timeD.second + 0.000001*timeD.microsecond)
            keyPressVector.append(seconds)

        except KeyboardInterrupt:
            print "Caught keyboard interupt"
            keyPressNumpy = np.asarray(keyPressVector)
            print "Converted to numpy"
            np.save('KeyPress', keyPressNumpy)
            print "saved numpy"
            break
        
def getKeyPressVector():
    return keyPressVector


if __name__=='__main__':
        KeyPress()
