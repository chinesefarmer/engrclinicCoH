import csv
from serial import *
import msvcrt as m


last_received = ''
last_received_tabbed = ''

#When opening the csv file, remember to select the delimiter as commas
#(open office is stupid and won't put the data in separate columns otherwise)
def csv_writer(data):
    with open(filename, 'a') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        writer.writerow(data)

#Set port and baudRate when calling this function
def receiving(port, baudRate):
    usb = Serial(port, baudRate)
    usb.timeout = 1
    global last_received
    buffer = ''
    csv_writer(["AcclX","AcclY","AcclZ","MagX","MagY","MagZ","GyroX","GyroY","GyroZ"])
    
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
                AcclX = float(last_received_tabbed[0])        
                AcclY = float(last_received_tabbed[1])
                AcclZ = float(last_received_tabbed[2])
                MagX = float(last_received_tabbed[3])       
                MagY = float(last_received_tabbed[4])
                MagZ = float(last_received_tabbed[5])
                GyroX = float(last_received_tabbed[6])        
                GyroY = float(last_received_tabbed[7])
                GyroZ1 = last_received_tabbed[8]         #Keep this line at the end
                if '\r' in GyroZ1:
                    GyroZBogus = GyroZ1.split('\r')
                    GyroZ = float(GyroZBogus[0])
                else:
                    GyroZ = float(GyroZ1)
                    
                print "Accl \t\t Mag \t\t Gyro"
                print "X: " + str(AcclX) + "\tX: " + str(MagX) + "\tX: " + str(GyroX)
                print "Y: " + str(AcclY) + "\tY: " + str(MagY) + "\tY: " + str(GyroY)
                print "Z: " + str(AcclZ) + "\tZ: " + str(MagZ) + "\tZ: " + str(GyroZ) + "\n"

                
                
                data = [AcclX, AcclY, AcclZ, MagX, MagY, MagZ, GyroX, GyroY, GyroZ]
                csv_writer(data)

            #buffer = lines[-1]
                

if __name__=='__main__':
    filename = raw_input('Enter a file name w/ .csv at the end:  ')
    receiving('COM3',57600)
    
