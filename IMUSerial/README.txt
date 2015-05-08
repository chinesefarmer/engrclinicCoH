This README file contains instructions on how to operate the headgear containing the IMU, the blink sensor,
and the webcam. Below there is also a short troubleshooting section on the most common problems.

Revising History
-----------------------------------
COH Clinic Team - May 8 2015


How to Operate:
-----------------------------------
1. Plug in the short blue USB sticking out of the headgear (this is connected to the teensy microprocessor) 
into the computer.

2. Plug in the longer black USB sticking out of the headgear (this is connected to the webcam).

3. Double-click GUI_main.py. This will cause the Graphical User Interface to appear.

4.





Troubleshooting:
-----------------------------------

Here are several problems that may be encaountered when using the designed headpiece.

Problem:
If double-clicking GUI_main.py causes a black window to quickly appear with some text and then crashes out

Solution:
Right-Click on the GUI_main.py and click on edit with IDLE. Then when the new window opens with the code,
click on the menu button Run>>Run Module. This will cause a 


Problem:
If this error shows on the screen of the python code:
SerialException: could not open port 'COM6': WindowsError(2, 
'The system cannot find the file specified.')

(The exception does not have to specify COM6 but can be any COM specified)


Solution:
First restart the computer. Run all the programs. 

If this doesn’t fix the problem, unplug the usb and plug it back in. Then open up the arduino sketch called 
sensorTracking.ino and press verify and then upload. Go to the menu and check under tools. If the serial 
port says com6, then go into the code running the GUI and check if com6 is being opened up. If a different 
com is being opened, then change it to com6 or whichever com was being displayed in the arduino sketch.

If it the serial port does not say anything, restart the computer and try these steps all over again.


Problem:
If this error shows on the screen: ZeroDivisionError: float division by zero

Solution:
Check if the CSV file includes identical time stamps for multiple data points. If so, you will not be able 
to run the blink algorithm on the saved data (e.g. test mode). 

Problem:
If no data is being sent through the serial communication to the computer or the data is unresponsive

Solution: 
1. Check that the usb cables are connected to the computer.
2. Check that the teensy is currently running the correct program.
	- This can be done by opening sensorTracking.ino and press verify and upload. Open the Serial
	Monitor.
3. If all the above checks have been made and fixing them did not fix the problem,
	you will need to open up the headgear carefully and check if the wires are all still connected.
	Refer to the wiring diagram included in the file and the teensy diagram to ensure that the wires
	are connected.




Need a teensy diagram
Need a wiring diagram

