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

import cmd
import subprocess
import shlex
import time
import wx
import datetime
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar
import matplotlib as mpl
import matplotlib.pyplot as plt
from serial import *
import csv
from math import *
import msvcrt as m
import numpy as np
import pylab as pl
import time as tm
from outputnumbers import SerialData
from copy import deepcopy

################################################################################
class MainFrame(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self,parent, title=title, size=(300,400))
        print "starting..."
        self.initSensors()

        #drawing the main panel
        sizerH = wx.BoxSizer(wx.HORIZONTAL)
        
        box = wx.StaticBox(self, -1, label = "Control Box")
        sizerV = wx.StaticBoxSizer(box, wx.VERTICAL)

        #init GUI Buttons
        StopBtn = wx.Button(self, label="Stop All Sensors")
        StopBtn.Bind(wx.EVT_BUTTON, self.stopAll )
        SaveBtn = wx.Button(self, label= "Save All Data")
        SaveBtn.Bind(wx.EVT_BUTTON, self.saveAll)

        sizerV.Add(StopBtn, 0,wx.ALIGN_CENTER|wx.ALL, 5)
        sizerV.AddSpacer(5,5)
        sizerV.Add(SaveBtn, 0,wx.ALIGN_CENTER|wx.ALL, 5)

        #init those sensor plots
        sizerDisplayV1 = wx.BoxSizer(wx.VERTICAL)
        sizerDisplayV2 = wx.BoxSizer(wx.VERTICAL)

        self.displayPanel1 = ColorPanel(self, source=self.data, focusIndex = self.pitchMaxIndex,percentIndex =self.combpitchYawIndex , timerSource = self.redraw_timer, title = "Focus on the Operating Field", xAxisLabel = "Percent Focus", yAxisLabel = "")
        sizerDisplayV2.Add(self.displayPanel1, 1, wx.EXPAND|wx.LEFT)
        
        sizerH.Add(sizerDisplayV1, 1, wx.EXPAND)
        sizerH.Add(sizerDisplayV2, 1, wx.EXPAND)
        
        sizerH.Add(sizerV, 0, wx.RIGHT, 0)
        self.SetSizerAndFit(sizerH)

        # Setting up the menu bar
        filemenu= wx.Menu()

        # wx.ID_ABOUT and wx.ID_EXIT are standard IDs provided by wxWidgets.
        filemenu.Append(wx.ID_ABOUT, "&About"," Information about this program")
        filemenu.AppendSeparator()
        item = filemenu.Append(wx.ID_EXIT,"E&xit"," Terminate the program")
        self.Bind(wx.EVT_MENU, self.onQuit, item)

        # Creating the menubar.
        menuBar = wx.MenuBar()
        menuBar.Append(filemenu,"&File") # Adding the "filemenu" to the MenuBar
        self.SetMenuBar(menuBar)  # Adding the MenuBar to the Frame content.

        self.Fit()
        self.Show(True)

    def initSensors(self):
        self.s = SerialData()
        self.data = self.s.next()

        self.redraw_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_redraw_timer, self.redraw_timer)        
        self.redraw_timer.Start(1) #refresh rate in ms
        
        self.paused = False
        self.gotData = False
        self.paused = False
        self.blinkIndex = 2

        self.smoothRindex = 3 
        self.smoothPindex = 4
        self.smoothYindex = 5

        self.pitchMaxIndex = 11
        self.pitchFocusIndex = 12
        self.yawMaxIndex = 13
        self.yawFocusIndex = 14
        self.combpitchYawIndex = 15

    def on_redraw_timer(self, event):
        # if paused do not add data, but still redraw the plot
        # (to respond to scale modifications, grid change, etc.)
        if not self.paused:
            try:    
                self.data = self.s.next()
                if(self.data[0] != 1):
                    pass    
                else:
                    self.gotData = True
                    self.displayPanel1.data = self.data
                    self.displayPanel1.refresh()

            except KeyboardInterrupt:
                pass

    def stopAll(self, event=None):
        """stop or start all plots"""
        self.paused = False if self.paused else True
        self.gotData = False
        label = "Resume all Sensors" if (~self.paused) else "Pause all Sensors"
        self.displayPanel1.paused = False if self.displayPanel1.paused else True
        pass

    def saveAll(self, event=None):
        """Save all the data"""
        self.s.end()

    def onQuit(self, event=None):
        """Exit"""
        self.Close()

################################################################################
class ColorPanel(wx.Panel):
    """ The graphing frames frame of the application
    """
    
    def __init__(self, parent, source, focusIndex = 0, percentIndex= 0, timerSource = [datetime.datetime.now().time()] , title = "Focus on the Operating Field in Degrees", xAxisLabel = "x axis", yAxisLabel = "y axis"):
        wx.Panel.__init__(self,parent, size =(500,50))
        self.focusIndex = focusIndex
        self.percentIndex = percentIndex

        self.data = source      
        self.time = [datetime.datetime.now().time()]

        self.sensorVal = self.data[percentIndex]
        self.sensorDist = self.data[focusIndex]
        self.sumVal = 0.0
        self.xmin = 0
        self.xmax =100 #Min to max is 100 datapoints exactly for percentages
        self.xcolorMax = 120
        self.ymin = 0
        self.ymax = 1
        self.res = 101
        self.medVal = 51 #medium value for coloring purposes.

        linAngle = np.ones(self.res)
        self.mesh = np.tile(linAngle,(self.ymax,1))
        self.title = title
        self.xAxisLabel = xAxisLabel
        self.yAxisLabel = yAxisLabel

        self.safe = False
        self.paused = False

        self.create_main_panel()        
        self.redraw_timer = wx.Timer(self)

    def create_main_panel(self):
        self.panel = wx.Panel(self)

        self.init_plot()
        
        self.canvas = FigCanvas(self, 0, self.fig)
        
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.canvas, 0, flag=wx.EXPAND)        
        
        self.SetSizer(self.vbox)
        self.vbox.Fit(self)

    def init_plot(self):
        self.dpi = 100
        self.fig = Figure((3.0, 3.0), dpi=self.dpi)

        self.axes_sensor1 = self.fig.add_subplot(111)
        self.axes_sensor1.set_axis_bgcolor('black')
        self.axes_sensor1.set_title(self.title, size=12)

        pl.setp(self.axes_sensor1.get_yticklabels(), visible= False)
        self.axes_sensor1.set_xlabel(self.xAxisLabel, size = 8)

        print "init ColorPanel", self.data, self.sensorVal
        currplot = self.mesh
        cmap = plt.get_cmap('jet_r')
        cmap.set_bad(color = 'k', alpha = 1)
        self.color_sensor = self.axes_sensor1.pcolormesh(currplot, cmap='jet_r', vmin = self.xmin, vmax=self.xcolorMax)

        self.axes_sensor1.set_xbound(lower=self.xmin, upper=self.xmax)
        self.axes_sensor1.set_ybound(lower=self.ymin, upper=self.ymax)

    def draw_plot(self):
        """ Redraws the plot
        """
        currplot = self.mesh * self.sensorVal
        currplot[:,self.sensorVal:] = np.nan

        currplot = np.ma.masked_invalid(currplot)
        self.color_sensor.set_array(currplot.ravel())
        self.axes_sensor1.set_xbound(lower=self.xmin, upper=self.xmax)
        self.axes_sensor1.set_ybound(lower=self.ymin, upper=self.ymax)

        self.canvas.draw()
        self.canvas.Refresh()
        self.pause = True


    def refresh(self):
        if not self.paused:
            try:    
                if(self.data[0] != 1):
                    pass
                else:
                    self.sensorVal = int(self.data[self.percentIndex]*100)
                    self.draw_plot()
            except KeyboardInterrupt:
                pass
################################################################################
def buildGUI():
    app = wx.App(False)
    frame = MainFrame(None, "Test Color bar plotting")
    app.MainLoop()

if __name__ == '__main__':
    buildGUI()