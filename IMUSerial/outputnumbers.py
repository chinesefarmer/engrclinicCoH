#!/usr/bin/env python27
################################################################################
# This piece of code is developed by the 2014-2015 City of Hope-Tracking team 
# from Harvey Mudd College
# It is used to create a GUI for displaying blinks with an IR blink sensor,
# displaying percentage focus in real time and streaming and recording data
# GUI_main.py requires GUI_colorBar.py and GUI_plotPanel.py to plot properly.
# It also requires the Spring_Blinksensor.py and Spring_IMUSensor.py, as well. 
# 
# As of hardware, the sensor package is required to run the program properly. 
# specifically, the arduino teensy 3.1 needs to be connected to one of the COM ports
# on the computer. The streaming camera logitech C615 needs to be connected for 
# camera streaming to work. 
# Additional arduino, python libraries also need to be installed. 
# Please see the installation section in the appendix of the final report for details.
# Code was last changed at:
# May 6, 2015, Claremont, California 
################################################################################

import random
import time



class SerialData(object):
	def __init__(self, init=50, length=16):
		self.dataSet = [] #IR1, IR2, IR3, light
		self.len = length

	def genRandom(self, rangeL, rangeH):
		return random.uniform(rangeL, rangeH)

	def next(self):
		self.genData(self.len)
		#self.genArray()
		#print "gennext"
		return self.dataSet

	
	def genData(self, length=15):
		newData = [1]
		for i in range(self.len-1):
			newData.append(self.genRandom(1, 50))
		newData[4] = self.genRandom(0, 360)
		newData[15] = self.genRandom(0,1)
		self.dataSet = newData


	def genArray(self, index=6):
		array = []
		for i in range(360):
			array.append(int(self.genRandom(0,100)))
		self.dataSet[index] = array


	def __del__(self):
		pass


if __name__ == '__main__':
	s = SerialData()
	while(1):
		try:
			s.next()
			print s.next()
			time.sleep(0.015)
		except KeyboardInterrupt:
			break
		