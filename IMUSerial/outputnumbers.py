#!/usr/bin/env python27
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
		