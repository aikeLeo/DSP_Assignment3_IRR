"""
Copyright (c) 2010, Tino de Bruijn
Copyright (c) 2018-2020, Bernd Porr <mail@berndporr.me.uk>

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
"""


import pyfirmata2

import sys

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from scipy import signal


# Realtime oscilloscope at a sampling rate of 100Hz
# It displays analog channel 0.
# You can plot multiple chnannels just by instantiating
# more RealtimePlotWindow instances and registering
# callbacks from the other channels.

class IIR2Filter():

    def __init__(self, coeff):
        self.coeff = coeff
        self.buffer1 = 0
        self.buffer2 = 0
        self.acc_input = 0
        self.output = 0

    def filter(self, x):
        # IIR part
        self.acc_input = x - (self.coeff[4] * self.buffer1) - (self.coeff[5] * self.buffer2)

        # FIR part
        self.output = self.acc_input * self.coeff[0] + (self.coeff[1] * self.buffer1) + (self.coeff[2] * self.buffer2)

        self.buffer2 = self.buffer1
        self.buffer1 = self.acc_input

        return self.output


class IIRFilter():

    def __init__(self, fc0, fc1, fc2):
        self.fc0 = fc0
        self.fc1 = fc1
        self.fc2 = fc2
        #self.sos = signal.butter(4, fc0*2, 'lowpass', output='sos')
        self.sos = signal.butter(4, [fc1 * 2, fc2 * 2], 'bandstop', output='sos')
        #self.sos = signal.butter(4, [self.fc1 * 2, self.fc2 * 2], 'bandpass', output='sos')
        self.y = [0] * len(self.sos)
        for i in range(len(self.y)):
            self.y[i] = IIR2Filter(self.sos[i])

    def filter(self, x):

        output = x
        for i in range(len(self.y)):
            output = self.y[i].filter(output)

        return output



PORT = pyfirmata2.Arduino.AUTODETECT
PIN = 7  # Pin 7 for Fan


#board = pyfirmata2.Arduino(PORT)

# Creates a scrolling data display
class RealtimePlotWindow:

    def __init__(self):
        # create a plot window
        self.fig, self.ax = plt.subplots()
        # that's our plotbuffer
        self.plotbuffer = np.zeros(500)
        # create an empty line
        self.line, = self.ax.plot(self.plotbuffer)
        # axis 轴
        self.ax.set_ylim(0, 1.5)
        # That's our ringbuffer which accumluates the samples
        # It's emptied every time when the plot window below
        # does a repaint
        self.ringbuffer = []
        # add any initialisation code here (filters etc)
        # start the animation
        self.ani = animation.FuncAnimation(self.fig, self.update, interval=100)

    # updates the plot
    def update(self, data):
        # add new data to the buffer
        self.plotbuffer = np.append(self.plotbuffer, self.ringbuffer)
        # only keep the 500 newest ones and discard the old ones
        self.plotbuffer = self.plotbuffer[-500:]
        self.ringbuffer = []
        # set the new 500 points of channel 9
        self.line.set_ydata(self.plotbuffer)
        return self.line,

    # appends data to the ringbuffer
    def addData(self, v):
        self.ringbuffer.append(v)


# Create an instance of an animated scrolling window
# To plot more channels just create more instances and add callback handlers below
# create 2 plot
realtimePlotWindow = RealtimePlotWindow()
realtimePlotWindow2 = RealtimePlotWindow()


# sampling rate: 100Hz
samplingRate = 100
# f cutoff
f0 = 50/250
f1 = 45/250
f2 = 55/250

# called for every new sample which has arrived from the Arduino
def callBack(data):

    realtimePlotWindow.addData(data)
    # add any filtering here:
    IIR = IIRFilter(f0, f1, f2)
    data2 = IIR.filter(data)
    # send the sample to the plotwindow
    realtimePlotWindow2.addData(data2)

    if data2 < 0.1:
        board.digital[PIN].write(1)
    else:
        board.digital[PIN].write(0)

# Get the Ardunio board.
board = pyfirmata2.Arduino(PORT)

# Set the sampling rate in the Arduino
board.samplingOn(1000 / samplingRate)

# Register the callback which adds the data to the animated plot
board.analog[0].register_callback(callBack)

# Enable the callback
board.analog[0].enable_reporting()

# show the plot and start the animation
plt.show()

# needs to be called to close the serial port
board.exit()

print("finished")

#read LDR data

#LDR_original_data = board.get_pin('a:0:i')
#LDR_original_data.read()
#print(LDR_original_data)



