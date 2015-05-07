import cmd
import subprocess
import shlex
import time
import wx
# The recommended way to use wx with mpl is with the WXAgg
# backend. 
#
# inherited from nicole's code
import datetime
import matplotlib
#matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar
import matplotlib as mpl
#import numpy as np
#import pylab as pl
import matplotlib.pyplot as plt
#Test data comes from here
#from FallSiteVisit_GUI import SerialData as IRserialData
#from outputnumbers import SerialData as genIRserialData

# from main_sensors
#import Spring_BlinkSensor as bs
#import Spring_IMUSensor as imu
from serial import *
import csv
from math import *
import msvcrt as m
import numpy as np
import pylab as pl
import time as tm

#from datetime import *
from outputnumbers import SerialData
from copy import deepcopy

################################################################################
class MainFrame(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self,parent, title=title, size=(300,400))
        print "starting..."
        self.initSensors()

        #drawing the main panel
        #resize them
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

        #self, parent, source, focusIndex, percentIndex, timerSource = [datetime.datetime.now().time()] , title = "Focus on the Operating Field in Degrees", xAxisLabel = "x axis", yAxisLabel = "y axis"
        self.displayPanel1 = ColorPanel(self, source=self.data, focusIndex = self.pitchMaxIndex,percentIndex =self.combpitchYawIndex , timerSource = self.redraw_timer, title = "Focus on the Operating Field", xAxisLabel = "Percent Focus", yAxisLabel = "")
        sizerDisplayV2.Add(self.displayPanel1, 1, wx.EXPAND|wx.LEFT)
        #self.displayPanel2 = BarPanel(self, source=self.data, index = self.pitchIndex, timerSource = self.redraw_timer, title = "Blink Sensor data vs Time", xAxisLabel = "Time (s)", yAxisLabel ="Blink")
        #sizerDisplayV1.Add(self.displayPanel2, 1, wx.EXPAND|wx.ALL)
        
        sizerH.Add(sizerDisplayV1, 1, wx.EXPAND)
        sizerH.Add(sizerDisplayV2, 1, wx.EXPAND)
        
        sizerH.Add(sizerV, 0, wx.RIGHT, 0)
        self.SetSizerAndFit(sizerH)

        # Setting up the menu bar
        filemenu= wx.Menu()

        # wx.ID_ABOUT and wx.ID_EXIT are standard IDs provided by wxWidgets.
        filemenu.Append(wx.ID_ABOUT, "&About"," Information about this program")
        #self.Bind(wx.EVT_MENU, self.OnAbout, menuItem)
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
        # Sensor inputs
        #self.s = sensorData()
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
                #print "recieved data", self.data
                if(self.data[0] != 1):
                    pass    
                else:
                    self.gotData = True
                    self.displayPanel1.data = self.data
                    #self.displayPanel2.data = self.data

                    self.displayPanel1.refresh()
                    #self.displayPanel2.refresh()

            except KeyboardInterrupt:
                pass

    def stopAll(self, event=None):
        """stop or start all plots"""
        self.paused = False if self.paused else True
        self.gotData = False
        label = "Resume all Sensors" if (~self.paused) else "Pause all Sensors"

        self.displayPanel1.paused = False if self.displayPanel1.paused else True
        #self.displayPanel2.paused = False if self.displayPanel2.paused else True
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
        #**************************
        self.time = [datetime.datetime.now().time()]

        #print "init", self.data
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
        #self.Bind(wx.EVT_TIMER, self.on_redraw_timer, self.redraw_timer)        
        #self.redraw_timer.Start(1) #refresh rate in ms

    def create_main_panel(self):
        self.panel = wx.Panel(self)

        self.init_plot()
        
        self.canvas = FigCanvas(self, 0, self.fig)
        
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        #self.vbox.AddSpacer(5,5)
        self.vbox.Add(self.canvas, 0, flag=wx.EXPAND)        
        #self.vbox.AddSpacer(5,5)
        
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
        #self.axes_sensor1.set_ylabel(self.yAxisLabel, size = 8)

        # plot the data as a line series, and save the reference 
        # to the plotted line series
        print "init ColorPanel", self.data, self.sensorVal
        #print self.sensorVal
        currplot = self.mesh
        cmap = plt.get_cmap('jet_r')
        cmap.set_bad(color = 'k', alpha = 1)
        #currplot[:,self.sensorVal:]=-1000
        self.color_sensor = self.axes_sensor1.pcolormesh(currplot, cmap='jet_r', vmin = self.xmin, vmax=self.xcolorMax)

        #plot = self.mesh[:,self.sensorVal:]
        self.axes_sensor1.set_xbound(lower=self.xmin, upper=self.xmax)
        self.axes_sensor1.set_ybound(lower=self.ymin, upper=self.ymax)

    def draw_plot(self):
        """ Redraws the plot
        """
        # when xmin is on auto, it "follows" xmax to produce a 
        # sliding window effect. therefore, xmin is assigned after
        # xmax
        #if self.ymax_control.is_auto():
        #    ymax = round(max(self.sensorVal1), 0) + 1
        #else:
        #    ymax = int(self.ymax_control.manual_value())

        #print "sensorVal", self.sensorVal
        #print "returntype:", len(self.bar_sensor), len(self.sensorVal)
        #print self.sensorVal
        #plot = self.mesh[:,self.sensorVal:]
        currplot = self.mesh * self.sensorVal
        #print "len currplot", len(currplot)
        currplot[:,self.sensorVal:] = np.nan

        currplot = np.ma.masked_invalid(currplot)
        #currplot[:,self.sensorVal:]=-100
        self.color_sensor.set_array(currplot.ravel())
        #self.color_sensor = self.axes_sensor1.pcolormesh(currplot, cmap=None, vmin = self.xmin, vmax=self.medVal)
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
                    #print "here"
                    self.sensorVal = int(self.data[self.percentIndex]*100)
                    #print "sensorVal", self.sensorVal
                    
                    self.draw_plot()
            except KeyboardInterrupt:
                pass

    def gaussian(self, x, mu, sig):
        return np.exp(-(x - mu)**2) / (2 * sig ** 2)
################################################################################
class BarPanel(wx.Panel):
    """ The graphing frames frame of the application
    """
    
    def __init__(self, parent, source, index = 0, timerSource = [datetime.datetime.now().time()] , title = "Display Data", xAxisLabel = "x axis", yAxisLabel = "y axis"):
        wx.Panel.__init__(self,parent)
        self.index = index

        N = 360 #360 datapoints
        self.ind = np.arange(N)
        self.width = np.ones(N)
        self.data = source      
        #**************************
        self.time = [datetime.datetime.now().time()]
        #
        #print "init", self.data
        self.sensorVal = self.data[index] 
        zeroArray = np.zeros(N)
        #if the input is an array of sensors, then plot an array of zeros
        self.sensorVal = self.sensorVal if (type(self.sensorVal)==type(zeroArray)) else zeroArray

        self.title = title
        self.xAxisLabel = xAxisLabel
        self.yAxisLabel = yAxisLabel

        self.safe = False
        self.paused = False

        self.create_main_panel()
        
        self.redraw_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_redraw_timer, self.redraw_timer)        
        self.redraw_timer.Start(1) #refresh rate in ms

    def create_main_panel(self):
        self.panel = wx.Panel(self)

        self.init_plot()
        
        self.canvas = FigCanvas(self, -1, self.fig)

        self.hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        #self.hbox1.Add(self.pause_button, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)

        self.hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.canvas, 1, flag=wx.LEFT | wx.TOP | wx.GROW)        
        self.vbox.Add(self.hbox1, 0, flag=wx.ALIGN_LEFT | wx.TOP)
        self.vbox.Add(self.hbox2, 0, flag=wx.ALIGN_LEFT | wx.TOP)
        
        self.SetSizer(self.vbox)
        self.vbox.Fit(self)

    def init_plot(self):
        self.dpi = 100
        self.fig = Figure((3.0, 3.0), dpi=self.dpi)

        self.axes_sensor1 = self.fig.add_subplot(111)
        self.axes_sensor1.set_axis_bgcolor('black')
        self.axes_sensor1.set_title(self.title, size=12)
        
        self.axes_sensor1.set_xlabel(self.xAxisLabel, size = 8)
        self.axes_sensor1.set_ylabel(self.yAxisLabel, size = 8)

        #self.axes_sensor1.
        #pl.setp(self.axes_sensor1.get_xticklabels(), fontsize=8)
        pl.setp(self.axes_sensor1.get_yticklabels(), fontsize=8)
        #pl.setp(self.axes_sensor2.get_xticklabels(), fontsize=8)
        #pl.setp(self.axes_sensor2.get_yticklabels(), fontsize=8)

        # plot the data as a line series, and save the reference 
        # to the plotted line series
        #
        print "init BarPanel", self.data, self.sensorVal
        #White = sensor
        #print self.sensorVal
    
        self.bar_sensor = self.axes_sensor1.bar(self.ind, self.sensorVal, self.width, 0,color='white') # this returns

    def draw_plot(self):
        """ Redraws the plot
        """
        # when xmin is on auto, it "follows" xmax to produce a 
        # sliding window effect. therefore, xmin is assigned after
        # xmax.
        xmin = 0
        xmax = 360
        ymin = 0
        ymax = 100
        maxSensorVal = max(self.sensorVal)

        #if self.ymax_control.is_auto():
        #    ymax = round(max(self.sensorVal1), 0) + 1
        #else:
        #    ymax = int(self.ymax_control.manual_value())

        self.bar_sensor.set_width = self.ind
        self.axes_sensor1.set_xbound(lower=xmin, upper=xmax)
        self.axes_sensor1.set_ybound(lower=ymin, upper=ymax)
        #print "sensorVal", self.sensorVal
        #print "returntype:", len(self.bar_sensor), len(self.sensorVal)
        #print self.sensorVal
        for rect, h in zip(self.bar_sensor, self.sensorVal):
            rect.set_height(h)
        self.canvas.draw()

    def on_redraw_timer(self, event):
        # if paused do not add data, but still redraw the plot
        # (to respond to scale modifications, grid change, etc.)
        if not self.paused:
            try:    
                if(self.data[0] != 1):
                    pass
                else:
                    #print "here"
                    self.sensorVal =self.data[self.index]
                    print self.sensorVal
                    self.draw_plot()
            except KeyboardInterrupt:
                pass
    def refresh(self):
        # if paused do not add data, but still redraw the plot
        # (to respond to scale modifications, grid change, etc.)
        if not self.paused:
            try:    
                if(self.data[0] != 1):
                    pass
                else:
                    #print "here"
                    self.sensorVal = self.data[self.index]
                    #print self.sensorVal
                    self.draw_plot()
            except KeyboardInterrupt:
                pass

################################################################################
def buildGUI():
    app = wx.App(False)
    frame = MainFrame(None, "editor")
    #frame = MyFrame(None, 'Small editor')
    app.MainLoop()

if __name__ == '__main__':
    buildGUI()