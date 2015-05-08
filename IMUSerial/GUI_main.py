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
# The recommended way to use wx with mpl is with the WXAgg
# backend. 
import datetime
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar
import matplotlib as mpl
import matplotlib.pyplot as plt

# from main_sensors
import Spring_BlinkSensor as bs
import Spring_IMUSensor as imu
from serial import *
import csv
from serial import *
from math import *
import msvcrt as m
import numpy as np
import pylab as pl
import time as tm
# improve lag by adding threading
from threading import *
from GUI_colorBar import ColorPanel 
from GUI_plotPanel import GraphPanel3x
from GUI_plotPanel import GraphPanel
from copy import *
from serial.tools import list_ports
# Button definitions
ID_START = wx.NewId()
ID_STOP = wx.NewId()
# Define notification event for thread completion
EVT_RESULT_ID = wx.NewId()
################################################################################
#iniitalize the threading events
def EVT_RESULT(win, func):
    """Define Result Event."""
    win.Connect(-1, -1, EVT_RESULT_ID, func)

class ResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""
    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_RESULT_ID)
        self.data = data

# Thread class that executes processing
class WorkerThread(Thread):
    """Worker Thread Class."""
    def __init__(self, notify_window, passedData):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self._notify_window = notify_window
        self._want_abort = False
        # data class
        self.s = sensorData()
        print "started thread..."
        # This starts the thread running on creation, but you could
        # also make the GUI thread responsible for calling this
        self.start()

    def run(self):
        """Run Worker Thread."""
        # This is the code executing in the new thread. Simulation of
        # a long process (well, 10s here) as a simple loop - you will
        # need to structure your processing so that you periodically
        # peek at the abort variable
        while not self._want_abort:
            try:  
                self.data = self.s.next()
                #print "recieved data", self.data
                if(self.data[0] != 1):
                    self.gotData = False
                    wx.PostEvent(self._notify_window, ResultEvent(None))
                else:
                    self.gotData = True
                    wx.PostEvent(self._notify_window, ResultEvent(self.data))
                pass
            except KeyboardInterrupt:
                print "trying to stop here...."
                wx.PostEvent(self._notify_window, ResultEvent(None))
                return
        #if exited out of loop, return nothing
        wx.PostEvent(self._notify_window, ResultEvent(None))
        self.s.end()
        return

    def abort(self):
        """abort worker thread."""
        print "aborting..."
        # Method for use by main thread to signal an abort
        self._want_abort = True
        #raise Exception('abort')

################################################################################
#initialize sensor reading and processing functions
class sensorData(object):
    def __init__(self):
        global filename,filenameIMU,filenameBlink
        print "initializing sensor data.........."
        dt = datetime.datetime.now()
        date = dt.strftime("%m%d%y_%H%M%p_")
        filenameIMU = date + 'imu.csv'

        #Reads the data to process for the blink sensor
        filenameBlink = date + 'blink.csv'

        #initialize teensy port...
        
        ports_avaiable = list(list_ports.comports())
        teensy_port = tuple()
        for port in ports_avaiable:
            if port[1].startswith("Teensy"):
                teensy_port = port

        if teensy_port:
            print "teensy ports:", teensy_port
            self.usb = Serial(teensy_port[0], 57600)
        else:
            print "Please check if sensor is plugged in correctly"
            self.usb = Serial('COM4', 57600) # The default COM port 4 is on the right
        self.blinkSensor = bs.BlinkSensor()
        self.blinkSensor.CheckKeyPress = False
        self.blinkSensor.filename = filenameBlink
        bs.initSerialConnection(self.usb, self.blinkSensor)
        self.imuSensor = imu.IMUSensor()
        self.imuSensor.filenameIMU = filenameIMU
        
        self.imuSensor.csv_writer(["AcclX","AcclY","AcclZ","MagX","MagY","MagZ","GyroX","GyroY","GyroZ", "Roll", "Pitch", "Yaw", "Time Elapsed(s)"],filenameIMU)
        

        # Settable values for blinkSensor 
        # How often to calculate the number of blinks, in minutes
        self.blinkSensor.tWindow = 1.0/3
        #How often to print number of blinks in last X minutes, where X is tWindow
        self.blinkSensor.tPrintBlink = 1.0/6

        self.prevBlinks = 0.0
        print "initialized Sensor"  

    def next(self):

        try:
            # serialData = [success,[IR, AcclX,AcclY,AcclZ,MagX,MagY,MagZ,GyroX,GyroY,GyroZ]]
            self.serialData = self.imuSensor.receiveSerial(self.usb)
            #print "got serial data"
            #Ensures that no errors are in the serialData array
            #serialData[0] == 1 means that there were no failures
            #serialData[0] == 0 means there was at least one failure            
            if(self.serialData[0] == 1):
                #[roll, pitch, self.nextY ,currTime, ready]
                IMUData = self.imuSensor.calcRPYData(self.serialData[1])
                #print "calculate IMU data"
                # Checks to see if the calibration period has ended
                if(IMUData[4] == 1):
                    # processedData = [smoothRoll,smoothPitch,smoothYaw,
                    # self.timeAtRoll,self.timeAtPitch,self.timeAtYaw, # THESE ARE 360 length array
                    # rollMax,rollFocus, pitchMax ,pitchFocus, yawMax ,yawFocus] # *Max is the focus angle and
                                                                        # *focus is the percent time focusing
                    processedData = self.imuSensor.processIMUData(IMUData)
                    #print "processed IMU data"
                    # Handles the IR Sensor
                    try:
                        IR1 = float((self.serialData[1])[0])
                        
                        numRecentBlinks = self.blinkSensor.Algorithm(IR1, False)
                        if(numRecentBlinks != 0):
                            self.prevBlinks = numRecentBlinks
                            combData = (processedData[11] + processedData[9])/2.0
                            outputData = [1,1] + [numRecentBlinks] + processedData + [combData]


                        else:
                            #print "trigger blink sensor data"
                            combData = (processedData[11] + processedData[9])/2.0
                            outputData = [1,1] + [self.prevBlinks] + processedData  + [combData]

                        #print "output withIR"
                    except ValueError:
                        combData = (processedData[11] + processedData[9])/2.0
                        outputData = [1,1] + [0] + processedData  + [combData]
                        print "Value Error"
                else:
                    #print "imu data not ready"
                    outputData =  [0,0] + [0,0,0,0,0,0,0,0,0,0,0,0,0,0]
            else:
                print "no sensor data"  
                outputData =  [0,0] + [0,0,0,0,0,0,0,0,0,0,0,0,0,0]
            return outputData
        #Run only at the end of the op  
        except KeyboardInterrupt:
            self.end()

    def end(self):
        self.usb.close()
        self.blinkSensor.saveFile()

        pass
        
################################################################################
#main frame for displaying the data
class MainFrame(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self,parent, title=title)
        # initialize menu bar
        self.CreateStatusBar() # A Statusbar in the bottom of the window

        self.initSensors()

        #resize them
        sizerH = wx.BoxSizer(wx.HORIZONTAL)
        box = wx.StaticBox(self, -1, label = "Control Box")
        sizerV = wx.StaticBoxSizer(box, wx.VERTICAL)

        #init GUI
        self.StopBtn = wx.Button(self, label="Stop Plotting")
        self.StopBtn.Bind(wx.EVT_BUTTON, self.stopAll )

        #this runs the threading for updating the sensor data
        sizerV.Add(self.pauseSensorBtn, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        sizerV.AddSpacer(5,5)
        sizerV.Add(self.startSensorBtn, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        sizerV.AddSpacer(5,5)

        # Draw the things        
        sizerV.Add(self.StopBtn, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        sizerV.AddSpacer(5,5)

        #add widgets        
        self.Panel3 = CameraPanel(self)
        sizerV.AddSpacer(5,5)
        sizerV.Add(self.Panel3, 0, wx.EXPAND)

        #init those sensor plots
        self.cb_color = wx.CheckBox(self, -1, "Show Color Grid",style=wx.ALIGN_RIGHT)
        self.Bind(wx.EVT_CHECKBOX, self.on_cb_color, self.cb_color)
        self.cb_color.SetValue(True)
        sizerV.Add(self.cb_color, 0, wx.EXPAND)

        self.sizerDisplayH1 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizerDisplayV2 = wx.BoxSizer(wx.VERTICAL)

        self.displayPanelBlink = GraphPanel(self, source=self.data, index = self.blinkIndex, timerSource = self.redraw_timer, title = "Blink Sensor data vs Time", xAxisLabel = "Time (s)", yAxisLabel ="Blink")
        self.sizerDisplayH1.Add(self.displayPanelBlink, 1, wx.EXPAND|wx.ALL)

        self.displayPanel1 = GraphPanel3x(self, source=self.data, index = [self.smoothRindex, self.smoothPindex, self.smoothYindex], timerSource = self.redraw_timer, title = "RPY data vs Time", xAxisLabel = "Time (s)", yAxisLabel = "Smooth RPY")
        self.sizerDisplayH1.Add(self.displayPanel1, 1, wx.EXPAND|wx.ALL)
        self.displayPanel2 = ColorPanel(self, source=self.data, focusIndex = self.pitchFocusIndex,percentIndex =self.combpitchYawIndex , timerSource = self.redraw_timer, title = "Focus on the Operating Field", xAxisLabel = "Percent Focus", yAxisLabel = "")
        self.sizerDisplayV2.Add(self.displayPanel2, 1, wx.EXPAND|wx.ALL)

        sizerH.Add(self.sizerDisplayH1, 1, wx.EXPAND)
        sizerH.Add(self.sizerDisplayV2, 1, wx.EXPAND)
        self.displayPanelBlink.Hide()
        self.displayPanel1.Hide()
        self.sizerDisplayH1.Hide(self)
        self.sizerDisplayH1.Layout()

        sizerH.Add(sizerV, 0, wx.RIGHT, 0)
        self.SetSizerAndFit(sizerH)
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
        self.data = np.zeros(16)
        self.worker = None
        self.startSensorBtn = wx.Button(self, ID_START, label="Start Sensors")
        self.pauseSensorBtn = wx.Button(self, ID_STOP, label="Stop Sensors and Save")
        self.Bind(wx.EVT_BUTTON, self.OnStart, id=ID_START)
        self.Bind(wx.EVT_BUTTON, self.OnStop, id=ID_STOP)
        # Set up event handler for any worker thread results
        EVT_RESULT(self,self.OnResult)

        self.redraw_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_redraw_timer, self.redraw_timer)        
        self.redraw_timer.Start(10) #refresh rate in ms
        self.startSensorBtn.Enable(True)
        self.pauseSensorBtn.Enable(False)

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


    def on_redraw_timer(self, event = None):
        if not self.paused:
            try:
                # comment out for therading    
                # self.data = self.s.next()
                if(self.data[0] != 1):
                    self.gotData = False
                    
                else:
                    self.gotData = True

                    showColor = self.cb_color.IsChecked()
                    if (showColor):
                        self.displayPanel2.data = self.data
                        #self.displayPanel3.data = self.data
                        #print "got data to main frame"
                        self.displayPanel2.refresh()
                        #self.displayPanel3.refresh()
                        pass
                    else: 
                        self.displayPanelBlink.data=self.data
                        self.displayPanel1.data=self.data
                        self.displayPanelBlink.refresh()
                        self.displayPanel1.refresh()
                        pass

            except KeyboardInterrupt:
                pass

    def on_cb_color(self, event = None):
        # if paused do not add data, but still redraw the plot
        # (to respond to scale modifications, grid change, etc.)
        showColor = self.cb_color.IsChecked()
        if (showColor):
            self.displayPanelBlink.Hide()
            self.displayPanel1.Hide()

            self.sizerDisplayH1.Hide(self)
            self.displayPanel2.Show()
            #self.displayPanel3.Show()
            self.sizerDisplayV2.Show(self)

            pass
        else:
            self.displayPanelBlink.Show()
            self.displayPanel1.Show()
            self.sizerDisplayH1.Show(self)
            self.displayPanel2.Hide()
            self.sizerDisplayV2.Hide(self)
            pass
        self.sizerDisplayH1.Layout()
        self.sizerDisplayV2.Layout()
        self.Layout()
        self.Fit()
        pass

    def stopAll(self, event = None):
        """stop or start all plots"""
        self.paused = not self.paused

        label = "Resume Plotting" if (self.paused) else "Pause Plotting"
        self.StopBtn.SetLabel(label)

        self.displayPanel1.paused = not self.displayPanel1.paused
        self.displayPanelBlink.paused = not self.displayPanelBlink.paused
        self.displayPanel2.paused = not self.displayPanel2.paused
        pass
        
    def OnStart(self, event = None):
        if not self.worker:
            print "starting Thread..."
            self.worker = WorkerThread(self, self.data)
            self.startSensorBtn.Enable(False)
            self.pauseSensorBtn.Enable(True)

    def OnStop(self, event = None):
        #print "trying to pause it?", self.worker
        if self.worker:
            self.worker.abort()
            self.worker = None
            self.startSensorBtn.Enable(True)
            self.pauseSensorBtn.Enable(False)

    def OnResult(self, event = None):
        if event.data == None:
            self.data = [0,0,0,0,0,0,0,0]
        else:
            #print "gotData", event.data[0:3]
            self.data = deepcopy(event.data)
            #self.on_redraw_timer()

    def onQuit(self, event=None):
        """Exit"""
        self.paused = True
        self.redraw_timer.Stop()
        self.saveAll()
        self.Close()
        frame.Destroy()

################################################################################
class CameraPanel(wx.Panel):
    """This panel holds Extra Controls for controlling the camera"""

    #----------------------------------------------------------------------
    def __init__(self, parent):
        """Constructor"""
        wx.Panel.__init__(self, parent)

        self.parent = parent  # Sometimes one can use inline Comments
        self.cameraStart = False

        self.CameraStartBtn = wx.Button(self, label="Start Stream")
        self.CameraStartBtn.Bind(wx.EVT_BUTTON, self.onStart)

        self.CameraStopBtn = wx.Button(self, label="Stop Stream")
        self.CameraStopBtn.Bind(wx.EVT_BUTTON, self.closeCamera)

        Sizer = wx.BoxSizer(wx.VERTICAL)
        Sizer.Add(self.CameraStartBtn, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        Sizer.Add(self.CameraStopBtn, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        self.CameraStartBtn.Enable(True)
        self.CameraStopBtn.Enable(False)
        self.SetSizerAndFit(Sizer)

    def onStart(self, event=None, saving = True):
        if not self.cameraStart:
            self.cameraStart = True
            self.CameraStartBtn.Enable(False)
            self.CameraStopBtn.Enable(True)
            dt = datetime.datetime.now()
            name = dt.strftime("\%m%d%Y_%H%M%p_")
            #else:
            #    name = self.directoryName

            stream = 'vlc.exe -I rc dshow:// :dshow-vdev="Logitech HD Webcam C615" :dshow-caching=200 :dshow-size=1280x720 :dshow-aspect-ratio=16\:9 :dshow-fps=30'

            save=' --sout=\"#duplicate{dst=display,dst=\'transcode{vcodec=h264,vb=1260,fps=30,size=1280x720}:std{access=file,mux=mp4,dst=' + 'C:\\\Users\\\HMC_clinic\\\Desktop' + name + 'TestLog_mp4.mp4}\'}\"'
            #name + '.mp4}\'}\"' #
            if saving:
             save = save
            else:
                save = ''

            command_line = stream + save
            #print command_line
            args = shlex.split(command_line)
            #print args
            p = subprocess.Popen(args)
            time.sleep(1)
            return 1

    #exit out of the streaming camera safetly
    def closeCamera(self, event=None):
        if self.cameraStart:
            self.cameraStart = False
            self.CameraStartBtn.Enable(True)
            self.CameraStopBtn.Enable(False)
            args = shlex.split('ivanbatch.bat')
            l = subprocess.call(args)
            time.sleep(1)
            return 1
            

    def OnMsgBtn(self, event=None):
        """Bring up a wx.MessageDialog with a useless message."""
        dlg = wx.MessageDialog(self,
                               message='A completely useless message',
                               caption='A Message Box',
                               style=wx.OK|wx.ICON_INFORMATION
                               )
        dlg.ShowModal()
        dlg.Destroy()
    
################################################################################
class BoundControlBox(wx.Panel):
    """ A static box with a couple of radio buttons and a text
        box. Allows to switch between an automatic mode and a 
        manual mode with an associated value.
    """
    def __init__(self, parent, ID, label, initval, checked = False):
        wx.Panel.__init__(self, parent, ID)
        
        self.value = initval
        
        box = wx.StaticBox(self, -1, label)
        sizer = wx.StaticBoxSizer(box, wx.HORIZONTAL)
        
        self.auto = wx.CheckBox(self, -1, label = "Auto", style=wx.ALIGN_RIGHT)
        self.auto.SetValue(checked)
        self.manual_text = wx.TextCtrl(self, -1, 
            size=(35,-1),
            value=str(initval),
            style=wx.TE_PROCESS_ENTER)
        
        self.Bind(wx.EVT_UPDATE_UI, self.on_update_manual_text, self.manual_text)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_text_enter, self.manual_text)
        
        sizer.Add(self.auto, 0, wx.EXPAND, 0)
        sizer.Add(self.manual_text, 0, wx.EXPAND, 0)
        
        self.SetSizer(sizer)
        sizer.Fit(self)
    
    def on_update_manual_text(self, event):
        self.manual_text.Enable(not self.auto.GetValue())
    
    def on_text_enter(self, event):
        self.value = self.manual_text.GetValue()
    
    def is_auto(self):
        return self.auto.GetValue()
        
    def manual_value(self):
        return self.value
################################################################################
def runCamera(name, saving=False):
    stream = 'vlc.exe -I rc dshow:// :dshow-vdev="Logitech HD Webcam C615" :dshow-caching=200 :dshow-size=1280x720 :dshow-aspect-ratio=16\:9 :dshow-fps=20'

    save=' --sout=\"#duplicate{dst=display,dst=\'transcode{vcodec=h264,vb=1260,fps=20,size=1280x720}:std{access=file,mux=mp4,dst=' + 'C:\\\Users\\\ClinicCoH\\\Desktop\\\TestLog_mp4.mp4}\'}\"'#name + '.mp4}\'}\"' #

    #save=' --sout=\"#duplicate{dst=display,dst=\'transcode{vcodec=h264,vb=1260,fps=30,size=1280x720}:std{access=file,mux=mp4,dst=C:\\\Users\\\ClinicCoH\\\Desktop\\\TestLog_mp4.mp4}\'}\"'

    if saving:
     save = save
    else:
        save = ''
    command_line = stream + save
    #print command_line
    args = shlex.split(command_line)
    #print args
    p = subprocess.Popen(args)
    time.sleep(1)
    return 1

def closeCamera():
        args = shlex.split('ivanbatch.bat')
        l = subprocess.call(args)
        time.sleep(1)
        return 1

################################################################################
def buildGUI():
    app = wx.App(False)
    frame = MainFrame(None, "Sensor Control Interface")
    app.MainLoop()

if __name__ == '__main__':
    buildGUI()

