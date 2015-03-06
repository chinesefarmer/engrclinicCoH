#!/usr/bin/env python27
import random
def genNums(rangeL, rangeH):
	return random.uniform(rangeL, rangeH)

if __name__ == '__main__':
    
    print genNums(1,104)
