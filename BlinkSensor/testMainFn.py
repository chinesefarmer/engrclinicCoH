test = True
from Spring_BlinkSensor import *

if __name__=='__main__':
    #Runs the algorithm on saved data, saving the results in a new excel file
    if(test):
        #Set the desired excel file to read data from
        filename = ('KatSession004bBlink.csv')
        BlinkSensor = BlinkSensor()
        BlinkSensor.testFileName = filename
        BlinkSensor.filename = filename
##        #Set the name for the output file
##        BlinkSensor.testFileName = ("Test2.csv")
##        BlinkSensor.saveBlinks([],1)
##        BlinkSensor.CheckKeyPress = False
##        data = BlinkSensor.csv_reader(2)
##        Hour = data[2]
##        Minute = data[3]
##        #Time here means seconds and microseconds
##        Time = data[0]
##        RawIR = data[1]
##        #Steps through the time vectors from the excel file and feeds both
##        #that and one IR value at a time to the algorithm
##        for i in range(len(data[0])):
##            BlinkSensor.minTestMode = (Hour[i]*60 + Minute[i] + Time[i]/60)
##            BlinkSensor.timeTestMode = Time[i]
##            BlinkSensor.Algorithm(RawIR[i],True)
##        BlinkSensor.saveTestFile()
        BlinkSensor.csv_reader(1)
    #Run the code live, while also running KeyPress.py to record when the
    #actual blinks are occuring. Only use this for calibration up to 1 minute
    #long.
    else:
        filename = raw_input('Enter a file name:  ')
        timeDate = datetime.now().date()
        filename = (str(timeDate)+filename+'.csv')

        #Change the name of the modem for your computer.
        usb = Serial('/dev/cu.usbmodem621',57600)

        BlinkSensorcsv_reader = BlinkSensor()
        BlinkSensor.filename = filename
        BlinkSensor.CheckKeyPress = False
        initSerialConnection(usb,BlinkSensor)


        while True:
            try:
                getSerial(usb, BlinkSensor)
            #Hit ctrl-c to end data collection and bring up a plot of results
            except KeyboardInterrupt:
                BlinkSensor.saveFile()
                BlinkSensor.csv_reader(1)
                usb.close()
                break
