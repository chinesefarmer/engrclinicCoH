#!/usr/bin/env python27
import random
def genNums(rangeL, rangeH):
	return random.uniform(rangeL, rangeH)


def main():
	randNum = genNums(1,104)
	print "number", randNum
	return randNum


if __name__ == '__main__':
	while(1):
		try:
			main()
		except KeyboardInterrupt:
			break
		