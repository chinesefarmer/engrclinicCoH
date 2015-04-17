#!/usr/bin/env python27
import random
import time



class SerialData(object):
	def __init__(self, init=50):
		self.dataSet = [] #IR1, IR2, IR3, light
		self.genData()

	def genRandom(self, rangeL, rangeH):
		return random.uniform(rangeL, rangeH)


	def genData(self):
		newData = []
		for i in range(4):
			newData.append(self.genRandom(1, 104))
		self.dataSet = newData

	def next(self):
		self.genData()
		#print "gennext"
		return self.dataSet

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
		