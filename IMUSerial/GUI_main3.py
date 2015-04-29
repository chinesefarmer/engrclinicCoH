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
# improve threading
from threading import *
from GUI_colorBar import ColorPanel 
from GUI_colorBar import BarPanel 
from GUI_plotPanel import GraphPanel3x
from GUI_plotPanel import GraphPanel

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
    def __init__(self, notify_window):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self._notify_window = notify_window
        self._want_abort = 0
        # This starts the thread running on creation, but you could
        # also make the GUI thread responsible for calling this
        self.start()

    def run(self):
        """Run Worker Thread."""
        # This is the code executing in the new thread. Simulation of
        # a long process (well, 10s here) as a simple loop - you will
        # need to structure your processing so that you periodically
        # peek at the abort variable
        for i in range(10):
            time.sleep(1)
            if self._want_abort:
                # Use a result of None to acknowledge the abort (of
                # course you can use whatever you'd like or even
                # a separate event type)
                wx.PostEvent(self._notify_window, ResultEvent(None))
                return
        # Here's where the result would be returned (this is an
        # example fixed result of the number 10, but it could be
        # any Python object)
        wx.PostEvent(self._notify_window, ResultEvent(10))

    def abort(self):
        """abort worker thread."""
        # Method for use by main thread to signal an abort
        self._want_abort = 1

################################################################################
#initialize sensor reading and processing functions
class sensorData(object):
    def __init__(self):
        global filename,filenameIMU,filenameBlink
        #Writes the raw data for the blink sensor
        #filename = raw_input('Enter a file name:  ')+ ".csv"
        
        #Writes the raw data for the IMU
        #filenameIMU = (filename[:-4] + 'IMU.csv' )
        print "initializing sensor data.........."
        filenameIMU = 'imu.csv'

        #Reads the data to process for the blink sensor
        #filenameBlink = (filename[:-4] + 'Blink.csv' )
        filenameBlink = 'blink.csv'

        self.usb = Serial('COM5', 57600)
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
        '''BEN: This is the loop I'm using right now to keep getting serial data and 
        then save it to a usb when the user hits ctrl-c (or keyboard interrupts the shell)'''       

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
                        #if(numRecentBlinks != 0):
                        #print "run blink sensor data"
                        if(numRecentBlinks != 0):
                            self.prevBlinks = numRecentBlinks
                            outputData = [1,1] + processedData[0:5]+ [numRecentBlinks]
                        else:
                            #print "trigger blink sensor data"
                            outputData = [1,1] + processedData[0:5] + [self.prevBlinks]

                        #print "output withIR"
                    except ValueError:
                        outputData = [1,1] + processedData[0:5] + [0]
                        print "Value Error"

                    # # Slows down the cycle enough to prevent divide by zero errors
                    # tm.sleep(.001)
                else:
                    #print "imu data not ready"
                    outputData =  [0,0] + [0,0,0,0,0,0]
            else:
                print "no sensor data"  
                outputData =  [0,0] + [0,0,0,0,0,0]
            
            #print "my outputs???", outputData
            #print "output data to main frame"
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
        wx.Frame.__init__(self,parent, title=title, size=(300,400))
        # initialize menu bar
        self.CreateStatusBar() # A Statusbar in the bottom of the window

        self.initSensors()

        #resize them
        sizerH = wx.BoxSizer(wx.HORIZONTAL)
        

        box = wx.StaticBox(self, -1, label = "Control Box")
        sizerV = wx.StaticBoxSizer(box, wx.VERTICAL)
        #init GUI
        self.StopBtn = wx.Button(self, label="Stop All Sensors")
        self.StopBtn.Bind(wx.EVT_BUTTON, self.stopAll )
        SaveBtn = wx.Button(self, label= "Save All Data")
        SaveBtn.Bind(wx.EVT_BUTTON, self.saveAll)

        #this runs the threading for updating the sensor data
        #self.startBtn = wx.Button(self, label="Start All Sensors")
        #self.startBtn.Bind(wx.EVT_BUTTON, self.startAll )
        
        #sizerV.Add(self.startBtn, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        #sizerV.AddSpacer(5,5)
        sizerV.Add(self.StopBtn, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        sizerV.AddSpacer(5,5)
        sizerV.Add(SaveBtn, 0,wx.ALIGN_CENTER|wx.ALL, 5)

        #add widgets        
        self.Panel3 = CameraPanel(self)
        sizerV.AddSpacer(5,5)
        sizerV.Add(self.Panel3, 0, wx.EXPAND)


        #init those sensor plots

        self.cb_color = wx.CheckBox(self, -1, "Show Color Grid",style=wx.ALIGN_RIGHT)
        self.Bind(wx.EVT_CHECKBOX, self.on_cb_color, self.cb_color)
        self.cb_color.SetValue(True)
        sizerV.Add(self.cb_color, 0, wx.EXPAND)

        sizerDisplayV1 = wx.BoxSizer(wx.VERTICAL)
        sizerDisplayV2 = wx.BoxSizer(wx.VERTICAL)

        self.displayPanelBlink = GraphPanel(self, source=self.data, index = self.blinkIndex, timerSource = self.redraw_timer, title = "Blink Sensor data vs Time", xAxisLabel = "Time (s)", yAxisLabel ="Blink")
        sizerDisplayV1.Add(self.displayPanelBlink, 1, wx.EXPAND|wx.ALL)
        
        self.displayPanel1 = GraphPanel3x(self, source=self.data, index = [self.smoothRindex, self.smoothPindex, self.smoothYindex], timerSource = self.redraw_timer, title = "RPY data vs Time", xAxisLabel = "Time (s)", yAxisLabel = "Smooth RPY")
        sizerDisplayV1.Add(self.displayPanel1, 1, wx.EXPAND|wx.ALL)
        #comment this out
        self.displayPanel2 =  ColorPanel(self, source=self.data, index = self.smoothYindex, timerSource = self.redraw_timer, title = "RPY data vs Time", xAxisLabel = "Time (s)", yAxisLabel = "Smooth RPY")
        sizerDisplayV1.Add(self.displayPanel2, 1, wx.EXPAND|wx.ALL)

        #self.displayPanel3 = BarPanel(self, source=self.data, index = self.pitchIndex, timerSource = self.redraw_timer, title = "Blink Sensor data vs Time", xAxisLabel = "Time (s)", yAxisLabel ="Blink")
        #sizerDisplayV1.Add(self.displayPanel3, 1, wx.EXPAND|wx.ALL)
        
        sizerH.Add(sizerDisplayV1, 1, wx.EXPAND)
        #sizerH.Add(sizerDisplayV2, 1, wx.EXPAND)
        
        sizerH.Add(sizerV, 0, wx.RIGHT, 0)
        self.SetSizerAndFit(sizerH)
        #self.Fit()
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
        self.s = sensorData()
        self.data = self.s.next()

        self.redraw_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_redraw_timer, self.redraw_timer)        
        self.redraw_timer.Start(0.01) #refresh rate in ms
        
        self.gotData = False
        self.paused = False
        self.blinkIndex = 7
        self.pitchIndex = 6
        self.smoothRindex = 4 
        self.smoothPindex = 3
        self.smoothYindex = 2

    #def bindEvents(self):
    #    self.Bind(wx.EVT_TIMER, self.on_redraw_timer, self.displayPanel1.redraw_timer)


    def on_redraw_timer(self, event):
        # if paused do not add data, but still redraw the plot
        # (to respond to scale modifications, grid change, etc.)
        if not self.paused:
            try:    
                self.data = self.s.next()
                #print "recieved data", self.data
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
                        
                    else: 
                        self.displayPanelBlink.data=self.data
                        self.displayPanel1.data=self.data
                        self.displayPanelBlink.refresh()
                        self.displayPanel1.refresh()

                    #self.displayPanelBlink.redraw_timer = self.redraw_timer
                    #self.displayPanel1.redraw_timer = self.redraw_timer

                    #print self.redraw_timer, self.displayPanel1.redraw_timer
            #pass

            except KeyboardInterrupt:
                pass

    def on_cb_color(self, event = None):
        # if paused do not add data, but still redraw the plot
        # (to respond to scale modifications, grid change, etc.)
        showColor = self.cb_color.IsChecked()
        if (showColor):
            self.displayPanelBlink.Hide()
            self.displayPanel1.Hide()
            self.displayPanel2.Show()
            #self.displayPanel3.Show()
        else:
            self.displayPanelBlink.Show()
            self.displayPanel1.Show()
            self.displayPanel2.Hide()
            #self.displayPanel3.Hide()
        self.Layout()
        pass

    def stopAll(self, event = None):
        """stop or start all plots"""
        #raise Exception 
        #self.gotData = False

        self.paused = not self.paused

        label = "Resume all Sensors" if (self.paused) else "Pause all Sensors"
        self.StopBtn.SetLabel(label)

        self.displayPanel1.paused = not self.displayPanel1.paused
        self.displayPanelBlink.paused = not self.displayPanelBlink.paused
        self.displayPanel2.paused = not self.displayPanel2.paused
        #self.displayPanel3.paused = not self.displayPanel3.paused
        pass
        
    def startAll(self, event = None):
        while not self.paused:
            try:  
                print "start all started"
                self.data = self.s.next()
                #print "recieved data", self.data
                if(self.data[0] != 1):
                    self.gotData = False
                    
                else:
                    self.gotData = True
                    #self.displayPanelBlink.data=self.data
                    #self.displayPanel1.data = self.data
                    #print "got data to main frame"
                    #self.displayPanelBlink.refresh()
                    #self.displayPanel1.refresh()
                    
                    #self.displayPanel2.data = self.data
                    #print "blinkData", self.data[self.smoothYindex]
                    #self.displayPanelBlink.redraw_timer = self.redraw_timer
                    #self.displayPanel1.redraw_timer = self.redraw_timer

                    #print self.redraw_timer, self.displayPanel1.redraw_timer
                #pass

            except KeyboardInterrupt:
                pass

    def saveAll(self, event=None):
        """Save all the data"""
        self.s.end()

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

        self.CameraStartBtn = wx.Button(self, label="Start Stream")
        self.CameraStartBtn.Bind(wx.EVT_BUTTON, self.onStart)

        self.CameraStopBtn = wx.Button(self, label="Stop Stream")
        self.CameraStopBtn.Bind(wx.EVT_BUTTON, self.closeCamera)

        ###
        self.directoryName = "C:\\\Users\\\jyang\\\Desktop\\\Log"
        self.name = ''
        self.textBox = wx.TextCtrl(self, -1, size=(140,-1))
        self.textBox.SetValue(self.name)
    
    #   self.lblname = wx.StaticText(self, label="Writing to:" + self.name))
        #dlg = wx.TextEntryDialog(parent, message, defaultValue=default_value)
        #dlg.ShowModal()
        #self.name = dlg.getValue
                
        Sizer = wx.BoxSizer(wx.VERTICAL)
        Sizer.Add(self.CameraStartBtn, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        Sizer.Add(self.CameraStopBtn, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        Sizer.Add(self.textBox)

        self.SetSizerAndFit(Sizer)
    # start stream and recording the camera
    def onStart(self, event=None):
        #self.name = self.textBox.GetValue()
        #if not self.name:
        #    dt = datetime.datetime.now()
        #    name = self.directoryName + dt.strftime("%m_%d_%Y_%H_%M%p")
        #else:
        #    name = self.directoryName

        stream = 'vlc.exe -I rc dshow:// :dshow-vdev="Logitech HD Webcam C615" :dshow-caching=200 :dshow-size=1280x720 :dshow-aspect-ratio=16\:9 :dshow-fps=20'

        save=' --sout=\"#duplicate{dst=display,dst=\'transcode{vcodec=h264,vb=1260,fps=20,size=1280x720}:std{access=file,mux=mp4,dst=' + 'C:\\\Users\\\ClinicCoH\\\Desktop\\\TestLog_mp4.mp4}\'}\"'#name + '.mp4}\'}\"' #

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
#def camera():
#   def __init__(self, parent):
#       self.p = subprocess.Popen() 
# vlc.exe -I rc dshow:// :dshow-vdev="Logitech HD Webcam C615" :dshow-caching=200 :dshow-size=1280x720 :dshow-aspect-ratio=16\:9 :dshow-fps=30 --sout="#duplicate{dst=display,dst='transcode{vcodec=h264,vb=1260,fps=30,size=1280x720}:std{access=file,mux=mp4,dst=C:\\Users\\jyang\\Desktop\\designReview-2.mp4}'}"
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

