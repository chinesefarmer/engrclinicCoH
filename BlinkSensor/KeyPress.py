import csv
from serial import *
from datetime import *
import time
import pylab as pl

keyPressVector = []

def KeyPress():
    blink = ''
    while True:
        blink = raw_input("Press enter if you blink.                    ")
        timeD = datetime.now().time()
        minutes = (timeD.hour*60 + timeD.minute +
                (timeD.second + 0.000001*timeD.microsecond)/60)
        keyPressVector.append(minutes)
        
def getKeyPressVector():
    return keyPressVector

