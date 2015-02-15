import csv
from serial import *
from math import *
import msvcrt as m
import numpy as np
import pylab as pl

from IMU_filter import activeFilter


pauseCheck = 0;                                 # Debug code


#When opening the csv file, remember to select the delimiter as commas
#(open office is stupid and won't put the data in separate columns otherwise)
def csv_writer(data):
    with open(filename, 'a') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        writer.writerow(data)

def csv_reader():
    with open(filename, 'r') as csv_file:
        reader = csv.reader(csv_file, delimiter = ',')
        next(reader)
        totData = []
        for row in reader:
            totData.append(row)
            print '' .join(row)

        print "done"
        print totData
        print len(totData)

        for row2 in totData:
            print row2
            print "acclX"
            print row2[0]

#Set port and baudRate when calling this function
def receiving(port, baudRate):
    #Initialize variables for roll, pitch, yaw calculations
    roll = 0; pitch = 0; yaw = 0; n = 0; nextR = 0; nextP = 0; nextY = 0; prevR = 0;
    prevP = 0; prevY = 0; gyroDriftX = 0; gyroDriftY = 0; gyroDriftZ = 0
##    AcclXTot = np.array([]);
##    AcclYTot = [];
##    AcclZTot = [];
##
##    GyroXTot = [];
##    GyroYTot = [];
##    GyroZTot = [];
##
##    MagXTot = [];
##    MagYTot = [];
##    MagZTot = [];
##
##    RollTot = [];
##    PitchTot = [];
##    YawTot = [];
    
    #Other important variables
    frequencyLoop = 5
    calibrationNo = 100
    usb = Serial(port, baudRate)
    usb.timeout = 1
    global last_received
    buffer = ''
    error = 0
    csv_writer(["AcclX","AcclY","AcclZ","MagX","MagY","MagZ","GyroX","GyroY","GyroZ", "Roll", "Pitch", "Yaw"])
    
    while True:

        #It also works if you just read the line instead of using a legit buffer
        buffer = usb.readline()
        #buffer = buffer + usb.read(usb.inWaiting())
        #raw_input("Press enter to continue...")
            
        if '\n' in buffer:
            lines = buffer.split('\n')
            last_received_full = lines[-2]

            if '\t' in last_received_full:
                last_received_tabbed = last_received_full.split('\t')
##                print(last_received_tabbed)
##                print len(last_received_tabbed)

                try:
                    GyroZ1 = last_received_tabbed[8]         #Keep this line at the end
                except IndexError:
##                    print "INDEX ERROR XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
                    continue
                
                if '\r' in GyroZ1:
                    GyroZBogus = GyroZ1.split('\r')
                    GyroZ = GyroZBogus[0]
                else:
                    GyroZ = GyroZ1
                try:
                    AcclX = float(last_received_tabbed[0])        
                    AcclY = float(last_received_tabbed[1])
                    AcclZ = float(last_received_tabbed[2])
                    MagX = float(last_received_tabbed[3])       
                    MagY = float(last_received_tabbed[4])
                    MagZ = float(last_received_tabbed[5])
                    GyroX = float(last_received_tabbed[6])        
                    GyroY = float(last_received_tabbed[7])
                    GyroZ = float(GyroZ)
                except ValueError:
##                    print "VALUE ERROR OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO"
                    continue


                if (n < 5):
                    n = n + 1
                elif(n == 6):
                    csv_reader()
                    break
                elif(n < calibrationNo):
                    n = n + 1
                    gyroDriftX = gyroDriftX + -1*GyroX
                    gyroDriftY = gyroDriftY + -1*GyroY
                    gyroDriftZ = gyroDriftZ + -1*GyroZ

                elif(n == calibrationNo):
                    n = n + 1
                    gyroDriftX = gyroDriftX + calibrationNo
                    gyroDriftY = gyroDriftY + calibrationNo
                    gyroDriftZ = gyroDriftZ + calibrationNo

                else:
                    
##                    global pauseCheck
##                    if(pauseCheck == 0):                                            #Debugging
####                        x = [1, 2, 3, 4, 5]
####
####                        y = [1, 4, 9, 16, 25]
####
####                        pl.plot(x, y)
####                        pl.show()
##                        pauseCheck = 1
##                        raw_input("Please put on Headset, then press enter:")        #Debugging

                    
                    n = n + 1
                    roll = atan2(AcclY, AcclZ)
                    if(AcclY*sin(roll) + AcclZ*cos(roll) == 0):
                        if(AcclX > 0):
                            pitch = pi/2
                        else:
                            pitch = -1*pi/2
                    else:
                        pitch = atan(-1*AcclX / (AcclY*sin(roll) + AcclZ*cos(roll)))
                    yaw = atan2(MagZ*sin(roll) - MagY*cos(roll), MagX*cos(pitch)+
                                MagY*sin(pitch)*sin(roll) + MagZ*sin(pitch)*cos(roll))

                    gX = abs(GyroX + gyroDriftX)
                    gY = abs(GyroY + gyroDriftY)
                    gZ = abs(GyroZ + gyroDriftZ)

                    prevR = nextR
                    prevP = nextP
                    prevY = nextY

                    nextR = (prevR + roll*gX) / (1 + gX)
                    nextP = (prevP + pitch * gY) / (1 + gY)
                    nextY = (prevY + yaw * gZ) / (1 + gZ)

                    roll = nextR*180/pi
                    pitch = -1*nextP*180/pi
                    yaw = nextY*180/pi
                    
                data = [AcclX, AcclY, AcclZ, MagX, MagY, MagZ, GyroX, GyroY, GyroZ, roll, pitch, yaw]
                data = activeFilter(data)
                csv_writer(data)



##                AcclXTot.append(AcclX);
##                if(n == 200):
##                    print len(AcclXTot)
##                    numSamples = np.linspace(1,200,200)
##                    print len(numSamples)
##                    print AcclXTot
##                    print numSamples
##                
##                    pl.plot(numSamples, AcclX)
##                    pl.show()

                print "-----------------------------------------" 
                print "Accl \t\t Mag \t\t Gyro"
                print "X: " + str(AcclX) + "  \tX: " + str(MagX) + "\tX: " + str(GyroX)
                print "Y: " + str(AcclY) + "  \tY: " + str(MagY) + "  \tY: " + str(GyroY)
                print "Z: " + str(AcclZ) + "  \tZ: " + str(MagZ) + "  \tZ: " + str(GyroZ) + "\n"
                print "Roll: " + str(roll) + "  \tPitch: " + str(pitch) + "  \tYaw: " + str(yaw)
                print "Sample Number is: " + str(n)
                print "-----------------------------------------"
                print " "



            #buffer = lines[-1]
                

if __name__=='__main__':
    filename = raw_input('Enter a file name:  ')+ ".csv"
    arduinoData = receiving('COM3',57600)






    
