#!/usr/bin/python3

from pyfirmata2 import Arduino
import time

PORT = Arduino.AUTODETECT
# PORT = '/dev/ttyACM0'


class AnalogPrinter:

    def __init__(self):
        # sampling rate: 10Hz
        self.samplingRate = 100
        self.timestamp = 0
        self.sum_num = 0
        self.jitter = 0
        # theorecal sampling dot is 100x10 = 1000
        self.theorecal_sample = self.samplingRate * 10
        self.board = Arduino(PORT)

    def start(self):
        self.board.analog[0].register_callback(self.myPrintCallback)
        self.board.samplingOn(1000 / self.samplingRate)
        self.board.analog[0].enable_reporting()

    def myPrintCallback(self, data):
        print("%f,%f" % (self.timestamp, data))
        self.timestamp += (1 / self.samplingRate)
        self.sum_num = self.timestamp
        self.jitter = (self.theorecal_sample - self.sum_num) / self.theorecal_sample
        print("The jitter is :", self.jitter, "%")

    def stop(self):
        self.board.samplingOff()
        self.board.exit()

print("Let's print data from Arduino's analogue pins for 10secs.")

# Let's create an instance
analogPrinter = AnalogPrinter()

# and start DAQ
analogPrinter.start()

#acquire data for 10secs
time.sleep(10)

analogPrinter.stop()

print("finished")
