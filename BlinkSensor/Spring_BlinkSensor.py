import csv
from serial import *
from datetime import *
import time

#YO TEAM!!!
#You must ALWAYS type usb.close() after you keyboard interrupt the code to quit
#otherwise you'll be forced to unplug and replug the sensor


#When opening the csv file, remember to select the delimiter as commas
#(open office is stupid and won't put the data in separate columns otherwise)
def csv_writer(data):
    with open(filename, 'a') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        writer.writerow(data)

#Set port and baudRate when calling this function
def receiving(usb):
    error = 0;
    usb.timeout = 1
    
    #This hopefully resets the Arduino
    usb.setDTR(False)
    time.sleep(1)
    usb.flushInput()
    usb.setDTR(True)
    
    buffer = ''
    csv_writer(["Hour","Minute","Second","Microsecond","IR1"])
    
    while True:
        #It also works if you just read the line instead of using a legit buffer
        buffer = usb.readline()
        #buffer = buffer + usb.read(usb.inWaiting())
        #raw_input("Press enter to continue...")

            
        if '\n' in buffer:
            lines = buffer.split('\n')
            IR1 = lines[-2]
            if '\r' in IR1:
                IR1Bogus = IR1.split('\r')
                if len(IR1Bogus) > 12:
                    print "Error"
                else:
                    try:
                        IR1 = float(IR1Bogus[0])
                    except ValueError:
                        error = 1
                        print "Value Error"
                        
            else:
                #print IR1
                try:
                    IR1 = float(IR1)
                except ValueError:
                    error = 1
                    print "Value Error"
                     

            timeD = datetime.now().time()
            if(error == 1):
                error = 0
            else:
                data = [timeD.hour,timeD.minute,timeD.second,timeD.microsecond,IR1]
                csv_writer(data)

                

if __name__=='__main__':
    filename = raw_input('Enter a file name w/ .csv at the end:  ')
    usb = Serial('/dev/cu.usbmodem621',57600)
    receiving(usb)
    

###We want Refresh_Interval_Ms to be the smallest possible, which is 1 millisecond
###At this rate we take samples every 0.12 seconds
###A blink is between 0.3 and 0.4 seconds long, which would explain why the height is different
###for blinks sometimes
##from datetime import *
##import os
##import pprint
##import random
##import sys
##import wx
##import xlwt
##import csv
##from serial import *
###import msvcrt as m
##
##REFRESH_INTERVAL_MS = 1
##
### The recommended way to use wx with mpl is with the WXAgg
### backend. 
##import matplotlib
##matplotlib.use('WXAgg')
##from matplotlib.figure import Figure
##from matplotlib.backends.backend_wxagg import \
##    FigureCanvasWxAgg as FigCanvas, \
##    NavigationToolbar2WxAgg as NavigationToolbar
##import numpy as np
##import pylab
##
###When opening the csv file, remember to select the delimiter as commas
###(open office is stupid and won't put the data in separate columns otherwise)
##def csv_writer(data):
##    with open(filename, 'a') as csv_file:
##        writer = csv.writer(csv_file, delimiter=',')
##        writer.writerow(data)
##    
###Set port and baudRate when calling this function
##def receiving(port, baudRate):
##    csv_writer(["Sample","Hour","Minute","Second","Microsecond","Raw IR1"])
##    usb = Serial(port, baudRate)
##    usb.timeout = 1
##    buffer = ''
##    
##    while True:
##        #It also works if you just read the line instead of using a legit buffer
##        buffer = usb.readline()
##            
##        if '\n' in buffer:
##            lines = buffer.split('\n')
##            IR1 = lines[-2]
##
##            if '\r' in IR1:
##                IR1Bogus = IR1.split('\r')
##                IR1 = float(IR1[0])
##            else:
##                IR1 = float(IR1)
##            buffer = lines[-1]
##            print IR1
##            return IR1
##
##class BoundControlBox(wx.Panel):
##    """ A static box with a couple of radio buttons and a text
##        box. Allows to switch between an automatic mode and a 
##        manual mode with an associated value.
##    """
##    def __init__(self, parent, ID, label, initval):
##        wx.Panel.__init__(self, parent, ID)
##        
##        self.value = initval
##        
##        box = wx.StaticBox(self, -1, label)
##        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
##        
##        self.radio_auto = wx.RadioButton(self, -1, 
##            label="Auto", style=wx.RB_GROUP)
##        self.radio_manual = wx.RadioButton(self, -1,
##            label="Manual")
##        self.manual_text = wx.TextCtrl(self, -1, 
##            size=(35,-1),
##            value=str(initval),
##            style=wx.TE_PROCESS_ENTER)
##        
##        self.Bind(wx.EVT_UPDATE_UI, self.on_update_manual_text, self.manual_text)
##        self.Bind(wx.EVT_TEXT_ENTER, self.on_text_enter, self.manual_text)
##        
##        manual_box = wx.BoxSizer(wx.HORIZONTAL)
##        manual_box.Add(self.radio_manual, flag=wx.ALIGN_CENTER_VERTICAL)
##        manual_box.Add(self.manual_text, flag=wx.ALIGN_CENTER_VERTICAL)
##        
##        sizer.Add(self.radio_auto, 0, wx.ALL, 10)
##        sizer.Add(manual_box, 0, wx.ALL, 10)
##        
##        self.SetSizer(sizer)
##        sizer.Fit(self)
##    
##    def on_update_manual_text(self, event):
##        self.manual_text.Enable(self.radio_manual.GetValue())
##    
##    def on_text_enter(self, event):
##        self.value = self.manual_text.GetValue()
##    
##    def is_auto(self):
##        return self.radio_auto.GetValue()
##        
##    def manual_value(self):
##        return self.value
##    
##
##
##class GraphFrame(wx.Frame):
##    """ The main frame of the application
##    """
##    title = 'Demo: dynamic matplotlib graph'
##    
##    def __init__(self):
##        wx.Frame.__init__(self, None, -1, self.title)
##
##        self.time = [datetime.now().time()]
##        self.IR1 = [receiving('/dev/cu.usbmodem621',57600)]
##
##        self.paused = False
##        
##        self.create_status_bar()
##        self.create_main_panel()
##        
##        self.redraw_timer = wx.Timer(self)
##        self.Bind(wx.EVT_TIMER, self.on_redraw_timer, self.redraw_timer)        
##        self.redraw_timer.Start(REFRESH_INTERVAL_MS)
##
##    def create_main_panel(self):
##        self.panel = wx.Panel(self)
##
##        self.init_plot()
##        self.canvas = FigCanvas(self.panel, -1, self.fig)
##
##        self.xmin_control = BoundControlBox(self.panel, -1, "X min", 0)
##        self.xmax_control = BoundControlBox(self.panel, -1, "X max", 50)
##        self.ymin_control = BoundControlBox(self.panel, -1, "Y min", 0)
##        self.ymax_control = BoundControlBox(self.panel, -1, "Y max", 100)
##        
##        self.pause_button = wx.Button(self.panel, -1, "Pause")
##        self.Bind(wx.EVT_BUTTON, self.on_pause_button, self.pause_button)
##        self.Bind(wx.EVT_UPDATE_UI, self.on_update_pause_button, self.pause_button)
##
##        self.cb_grid = wx.CheckBox(self.panel, -1, 
##            "Show Grid",
##            style=wx.ALIGN_RIGHT)
##        self.Bind(wx.EVT_CHECKBOX, self.on_cb_grid, self.cb_grid)
##        self.cb_grid.SetValue(True)
##        
##        self.cb_xlab = wx.CheckBox(self.panel, -1, 
##            "Show X labels",
##            style=wx.ALIGN_RIGHT)
##        self.Bind(wx.EVT_CHECKBOX, self.on_cb_xlab, self.cb_xlab)        
##        self.cb_xlab.SetValue(True)
##        
##        self.hbox1 = wx.BoxSizer(wx.HORIZONTAL)
##        self.hbox1.Add(self.pause_button, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
##        self.hbox1.AddSpacer(20)
##        self.hbox1.Add(self.cb_grid, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
##        self.hbox1.AddSpacer(10)
##        self.hbox1.Add(self.cb_xlab, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
##        
##        self.hbox2 = wx.BoxSizer(wx.HORIZONTAL)
##        self.hbox2.Add(self.xmin_control, border=5, flag=wx.ALL)
##        self.hbox2.Add(self.xmax_control, border=5, flag=wx.ALL)
##        self.hbox2.AddSpacer(24)
##        self.hbox2.Add(self.ymin_control, border=5, flag=wx.ALL)
##        self.hbox2.Add(self.ymax_control, border=5, flag=wx.ALL)
##        
##        self.vbox = wx.BoxSizer(wx.VERTICAL)
##        self.vbox.Add(self.canvas, 1, flag=wx.LEFT | wx.TOP | wx.GROW)        
##        self.vbox.Add(self.hbox1, 0, flag=wx.ALIGN_LEFT | wx.TOP)
##        self.vbox.Add(self.hbox2, 0, flag=wx.ALIGN_LEFT | wx.TOP)
##        
##        self.panel.SetSizer(self.vbox)
##        self.vbox.Fit(self)
##    
##    def create_status_bar(self):
##        self.statusbar = self.CreateStatusBar()
##
##    def init_plot(self):
##        self.dpi = 100
##        self.fig = Figure((3.0, 3.0), dpi=self.dpi)
##
##        self.axes = self.fig.add_subplot(111)
##        self.axes.set_axis_bgcolor('black')
##        self.axes.set_title('Blink Sensor', size=12)
##        
##        pylab.setp(self.axes.get_xticklabels(), fontsize=8)
##        pylab.setp(self.axes.get_yticklabels(), fontsize=8)
##
##        # plot the data as a line series, and save the reference 
##        # to the plotted line series
##        self.plot_IR1 = self.axes.plot(
##            self.IR1, 
##            linewidth=1,
##            color='white')[0]
##
##    def draw_plot(self):
##        """ Redraws the plot
##        """
##        # when xmin is on auto, it "follows" xmax to produce a 
##        # sliding window effect. therefore, xmin is assigned after
##        # xmax.
##        #
##        if self.xmax_control.is_auto():
##            xmax = len(self.IR1) if len(self.IR1) > 50 else 50
##        else:
##            xmax = int(self.xmax_control.manual_value())
##            
##        if self.xmin_control.is_auto():            
##            xmin = xmax - 50
##        else:
##            xmin = int(self.xmin_control.manual_value())
##
##        if self.ymin_control.is_auto():
##            ymin = round(min(self.IR1), 0) - 1
##        else:
##            ymin = int(self.ymin_control.manual_value())
##        
##        if self.ymax_control.is_auto():
##            ymax = round(max(self.IR1), 0) + 1
##        else:
##            ymax = int(self.ymax_control.manual_value())
##
##        self.axes.set_xbound(lower=xmin, upper=xmax)
##        self.axes.set_ybound(lower=ymin, upper=ymax)
##        
##        # anecdote: axes.grid assumes b=True if any other flag is
##        # given even if b is set to False.
##        # so just passing the flag into the first statement won't
##        # work.
##        #
##        if self.cb_grid.IsChecked():
##            self.axes.grid(True, color='gray')
##        else:
##            self.axes.grid(False)
##
##        # Using setp here is convenient, because get_xticklabels
##        # returns a list over which one needs to explicitly 
##        # iterate, and setp already handles this.
##        #  
##        pylab.setp(self.axes.get_xticklabels(), 
##            visible=self.cb_xlab.IsChecked())
##        
##        self.plot_IR1.set_xdata(np.arange(len(self.IR1)))
##        self.plot_IR1.set_ydata(np.array(self.IR1))
##        
##        self.canvas.draw()
##    
##    def on_pause_button(self, event):
##        self.paused = not self.paused
##
##    def on_update_pause_button(self, event):
##        label = "Resume" if self.paused else "Pause"
##        self.pause_button.SetLabel(label)
##    
##    def on_cb_grid(self, event):
##        self.draw_plot()
##    
##    def on_cb_xlab(self, event):
##        self.draw_plot()
##
##        
##    def on_redraw_timer(self, event):
##        # if paused do not add data, but still redraw the plot
##        # (to respond to scale modifications, grid change, etc.)
##        #
##        if not self.paused:
##            self.IR1.append(receiving('/dev/cu.usbmodem621',57600))
##            self.time.append(datetime.now().time())
##            data = [len(self.IR1),self.time[-1].hour(),self.time[-1].minute(),self.time[-1].second(),self.time[-1].microsecond(),self.IR1[-1]]
##            csv_writer(data)
##            print self.IR1[-1]
##                
##        self.draw_plot()
##    
##    def on_exit(self, event):
##        self.Destroy()
##    
##    def flash_status_message(self, msg, flash_len_ms=1500):
##        self.statusbar.SetStatusText(msg)
##        self.timeroff = wx.Timer(self)
##        self.Bind(
##            wx.EVT_TIMER, 
##            self.on_flash_status_off, 
##            self.timeroff)
##        self.timeroff.Start(flash_len_ms, oneShot=True)
##    
##    def on_flash_status_off(self, event):
##        self.statusbar.SetStatusText('')
##
##
##if __name__ == '__main__':
##    filename = raw_input('Enter a file name w/ .csv at the end:  ')
##    app = wx.PySimpleApp()
##    app.frame = GraphFrame()
##    app.frame.Show()
##    app.MainLoop()
##
