"""
Author: Ben Teng
Date: 2/9/15

Purpose: This will be called by the IMU_Write_Working.py function
(update this to match the function that takes a 9DOF
IMU printing serial data and saves the numbers to a
CSV file) which will pass a vector called data.

data = [AcclX, AcclY, AcclZ, MagX, MagY, MagZ, GyroX,
        GyroY, GyroZ]

This code will take this data and filter just the X,Y, and
Z of the Accerometer, the Magnetometer and the gyroscope.
"""

import csv
from serial import *
from math import *
import msvcrt as m

def activeFilter(data):
    return data
