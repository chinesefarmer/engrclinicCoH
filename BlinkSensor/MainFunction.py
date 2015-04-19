test = True
from Spring_BlinkSensor import *

if __name__=='__main__':
    if(test):
        filename = ('2015-04-10Jessica5.csv')
        BlinkSensor = BlinkSensor()
        BlinkSensor.filename = filename
        BlinkSensor.testFileName = ("Test2.csv")
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
        BlinkSensor.saveTestFile()
        BlinkSensor.csv_reader(1)
    else:
        filename = raw_input('Enter a file name:  ')
        timeDate = datetime.now().date()
        filename = (str(timeDate)+filename+'.csv')

        usb = Serial('/dev/cu.usbmodem621',57600)

        BlinkSensor = BlinkSensor()
        BlinkSensor.filename = filename
        BlinkSensor.CheckKeyPress = True
        initSerialConnection(usb,BlinkSensor)


        while True:
            try:
                getSerial(usb, BlinkSensor)
            except KeyboardInterrupt:
                BlinkSensor.saveFile()
                BlinkSensor.csv_reader(1)
                usb.close()
                break
