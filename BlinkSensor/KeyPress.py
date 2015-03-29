import csv
from serial import *
from datetime import *
import time
import pylab as pl
import numpy as np

keyPressVector = []

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
#    while True:
        KeyPress()
