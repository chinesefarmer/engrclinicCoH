"""
GP:
Changed datasource, title, and refresh interval to use
as a poor man's Arduino oscilliscope.

This demo demonstrates how to draw a dynamic mpl (matplotlib) 
plot in a wxPython application.

It allows "live" plotting as well as manual zooming to specific
regions.

Both X and Y axes allow "auto" or "manual" settings. For Y, auto
mode sets the scaling of the graph to see all the data points.
For X, auto mode makes the graph "follow" the data. Set it X min
to manual 0 to always see the whole data from the beginning.

Note: press Enter in the 'manual' text box to make a new value 
affect the plot.

Eli Bendersky (eliben@gmail.com)
License: this code is in the public domain
Last modified: 31.07.2008
"""
import os
import pprint
import random
import sys
import wx
import xlwt


REFRESH_INTERVAL_MS = 90

# The recommended way to use wx with mpl is with the WXAgg
# backend. 
#

import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar
import pylab
import numpy as np
#Data comes from here
from IMU_Write import SerialData as DataGen

def output(time_in, IR_in, blink_in, light_in, glance_in):
    workbook = xlwt.Workbook()
    sh = workbook.add_sheet('Test')

    style = xlwt.easyxf('font: bold 1')
    sh.write(0, 0, 'Time', style) # row, column, value
    sh.write(0, 1, 'Raw IR', style)
    sh.write(0, 2, 'Blink Alg', style)
    sh.write(0, 3, 'Raw Light Sensor', style)
    sh.write(0, 4, 'Glance Alg', style)
    minInput = min(len(time_in),len(IR_in),len(blink_in),len(light_in),len(glance_in))
    #for sec in time_in:
    for el in range(0,minInput):
        sh.write(el+1, 0, time_in[el]) #row, column, value
        sh.write(el+1, 1, IR_in[el])
        sh.write(el+1, 2, blink_in[el])
        sh.write(el+1, 3, light_in[el])
        sh.write(el+1, 4, glance_in[el])
    workbook.save('Test2.xls')

class BoundControlBox(wx.Panel):
    """ A static box with a couple of radio buttons and a text
        box. Allows to switch between an automatic mode and a 
        manual mode with an associated value.
    """
    def __init__(self, parent, ID, label, initval):
        wx.Panel.__init__(self, parent, ID)
        
        self.value = initval
        
        box = wx.StaticBox(self, -1, label)
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        
        self.radio_auto = wx.RadioButton(self, -1, 
            label="Auto", style=wx.RB_GROUP)
        self.radio_manual = wx.RadioButton(self, -1,
            label="Manual")
        self.manual_text = wx.TextCtrl(self, -1, 
            size=(35,-1),
            value=str(initval),
            style=wx.TE_PROCESS_ENTER)
        
        self.Bind(wx.EVT_UPDATE_UI, self.on_update_manual_text, self.manual_text)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_text_enter, self.manual_text)
        
        manual_box = wx.BoxSizer(wx.HORIZONTAL)
        manual_box.Add(self.radio_manual, flag=wx.ALIGN_CENTER_VERTICAL)
        manual_box.Add(self.manual_text, flag=wx.ALIGN_CENTER_VERTICAL)
        
        sizer.Add(self.radio_auto, 0, wx.ALL, 10)
        sizer.Add(manual_box, 0, wx.ALL, 10)
        
        self.SetSizer(sizer)
        sizer.Fit(self)
    
    def on_update_manual_text(self, event):
        self.manual_text.Enable(self.radio_manual.GetValue())
    
    def on_text_enter(self, event):
        self.value = self.manual_text.GetValue()
    
    def is_auto(self):
        return self.radio_auto.GetValue()
        
    def manual_value(self):
        return self.value


class GraphFrame(wx.Frame):
    """ The main frame of the application
    """
    title = 'Demo: dynamic matplotlib graph'
    
    def __init__(self):
        wx.Frame.__init__(self, None, -1, self.title)
        
        self.datagen = DataGen()
        #Remember, this comes in the form [IR1, IR2, IR3, light]
        self.data = self.datagen.next()
        self.IR1 = [self.data[0]]
        self.lightAvg = 0
        self.light = [self.data[3]]
        self.blink = []
        self.glance = []
        self.average = 0
        self.avg3 = 0
        self.avg3_cur = self.light[0]
        
        self.safe = False
        self.paused = False
        self.calibrate = True
        self.calibrateIdx = 1
        self.avg3Idx = 1
        
        self.create_menu()
        self.create_status_bar()
        self.create_main_panel()
        
        self.redraw_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_redraw_timer, self.redraw_timer)        
        self.redraw_timer.Start(REFRESH_INTERVAL_MS)

    def create_menu(self):
        self.menubar = wx.MenuBar()
        
        menu_file = wx.Menu()
        m_expt = menu_file.Append(-1, "&Save plot\tCtrl-S", "Save plot to file")
        self.Bind(wx.EVT_MENU, self.on_save_plot, m_expt)
        menu_file.AppendSeparator()
        m_save = menu_file.Append(-1, "Save data")
        self.Bind(wx.EVT_MENU, self.on_save_data, m_save)
        menu_file.AppendSeparator()
        m_exit = menu_file.Append(-1, "E&xit\tCtrl-X", "Exit")
        self.Bind(wx.EVT_MENU, self.on_exit, m_exit)
                
        self.menubar.Append(menu_file, "&File")
        self.SetMenuBar(self.menubar)

    def create_main_panel(self):
        self.panel = wx.Panel(self)

        self.init_plot()
        self.canvas = FigCanvas(self.panel, -1, self.fig)

        self.xmin_control = BoundControlBox(self.panel, -1, "X min", 0)
        self.xmax_control = BoundControlBox(self.panel, -1, "X max", 50)
        self.ymin_control = BoundControlBox(self.panel, -1, "Y min", 0)
        self.ymax_control = BoundControlBox(self.panel, -1, "Y max", 100)
        
        self.pause_button = wx.Button(self.panel, -1, "Pause")
        self.Bind(wx.EVT_BUTTON, self.on_pause_button, self.pause_button)
        self.Bind(wx.EVT_UPDATE_UI, self.on_update_pause_button, self.pause_button)

        self.calibrate_button = wx.Button(self.panel, -1, "Calibrate")
        self.Bind(wx.EVT_BUTTON, self.on_calibrate_button, self.calibrate_button)
        
        self.cb_grid = wx.CheckBox(self.panel, -1, 
            "Show Grid",
            style=wx.ALIGN_RIGHT)
        self.Bind(wx.EVT_CHECKBOX, self.on_cb_grid, self.cb_grid)
        self.cb_grid.SetValue(True)
        
        self.cb_xlab = wx.CheckBox(self.panel, -1, 
            "Show X labels",
            style=wx.ALIGN_RIGHT)
        self.Bind(wx.EVT_CHECKBOX, self.on_cb_xlab, self.cb_xlab)        
        self.cb_xlab.SetValue(True)
        
        self.hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox1.Add(self.pause_button, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.hbox1.AddSpacer(20)
        self.hbox1.Add(self.calibrate_button, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.hbox1.AddSpacer(20)
        self.hbox1.Add(self.cb_grid, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.hbox1.AddSpacer(10)
        self.hbox1.Add(self.cb_xlab, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        
        self.hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox2.Add(self.xmin_control, border=5, flag=wx.ALL)
        self.hbox2.Add(self.xmax_control, border=5, flag=wx.ALL)
        self.hbox2.AddSpacer(24)
        self.hbox2.Add(self.ymin_control, border=5, flag=wx.ALL)
        self.hbox2.Add(self.ymax_control, border=5, flag=wx.ALL)
        
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.canvas, 1, flag=wx.LEFT | wx.TOP | wx.GROW)        
        self.vbox.Add(self.hbox1, 0, flag=wx.ALIGN_LEFT | wx.TOP)
        self.vbox.Add(self.hbox2, 0, flag=wx.ALIGN_LEFT | wx.TOP)
        
        self.panel.SetSizer(self.vbox)
        self.vbox.Fit(self)
    
    def create_status_bar(self):
        self.statusbar = self.CreateStatusBar()

    def init_plot(self):
        self.dpi = 100
        self.fig = Figure((3.0, 3.0), dpi=self.dpi)

        self.axes = self.fig.add_subplot(121)
        self.axes_lightSensor = self.fig.add_subplot(122)
        self.axes.set_axis_bgcolor('black')
        self.axes_lightSensor.set_axis_bgcolor('black')
        self.axes.set_title('Blink Sensor', size=12)
        self.axes_lightSensor.set_title('Light Sensor', size=12)
        
        pylab.setp(self.axes.get_xticklabels(), fontsize=8)
        pylab.setp(self.axes.get_yticklabels(), fontsize=8)
        pylab.setp(self.axes_lightSensor.get_xticklabels(), fontsize=8)
        pylab.setp(self.axes_lightSensor.get_yticklabels(), fontsize=8)

        # plot the data as a line series, and save the reference 
        # to the plotted line series
        #
        print(self.data)
        #White = IR1
        self.plot_IR1 = self.axes.plot(
            self.IR1, 
            linewidth=1,
            color='white')[0]

        self.plot_blink = self.axes.plot(
            self.blink,
            linewidth = 2,
            color = 'gray')[0]

        self.plot_light = self.axes_lightSensor.plot(
            self.light,
            linewidth = 1,
            color = 'white')[0]

        self.plot_glance = self.axes_lightSensor.plot(
            self.glance,
            linewidth = 2,
            color = 'gray')[0]
            
            

    def draw_plot(self):
        """ Redraws the plot
        """
        # when xmin is on auto, it "follows" xmax to produce a 
        # sliding window effect. therefore, xmin is assigned after
        # xmax.
        #
        if self.xmax_control.is_auto():
            xmax = len(self.IR1) if len(self.IR1) > 50 else 50
        else:
            xmax = int(self.xmax_control.manual_value())
            
        if self.xmin_control.is_auto():            
            xmin = xmax - 50
        else:
            xmin = int(self.xmin_control.manual_value())


        # for ymin and ymax, find the minimal and maximal values
        # in the data set and add a mininal margin.
        # 
        # note that it's easy to change this scheme to the 
        # minimal/maximal value in the current display, and not
        # the whole data set.
        # 
        if self.ymin_control.is_auto():
            ymin = round(min(self.IR1), 0) - 1
        else:
            ymin = int(self.ymin_control.manual_value())
        
        if self.ymax_control.is_auto():
            ymax = round(max(self.IR1), 0) + 1
        else:
            ymax = int(self.ymax_control.manual_value())

        self.axes.set_xbound(lower=xmin, upper=xmax)
        self.axes.set_ybound(lower=ymin, upper=ymax)
        self.axes_lightSensor.set_xbound(lower=xmin, upper=xmax)
        #****Change this later
        self.axes_lightSensor.set_ybound(lower=round(min(min(self.light),min(self.glance)),0)-1,
                                         upper=round(max(max(self.light),max(self.glance)),0)+1)
        
        # anecdote: axes.grid assumes b=True if any other flag is
        # given even if b is set to False.
        # so just passing the flag into the first statement won't
        # work.
        #
        if self.cb_grid.IsChecked():
            self.axes.grid(True, color='gray')
            self.axes_lightSensor.grid(True, color='gray')
        else:
            self.axes.grid(False)
            self.axes_lightSensor.grid(False)

        # Using setp here is convenient, because get_xticklabels
        # returns a list over which one needs to explicitly 
        # iterate, and setp already handles this.
        #  
        pylab.setp(self.axes.get_xticklabels(), 
            visible=self.cb_xlab.IsChecked())
        
        self.plot_IR1.set_xdata(np.arange(len(self.IR1)))
        self.plot_IR1.set_ydata(np.array(self.IR1))
        self.plot_blink.set_xdata(np.arange(len(self.blink)))
        self.plot_blink.set_ydata(np.array(self.blink))
        self.plot_light.set_xdata(np.arange(len(self.light)))
        self.plot_light.set_ydata(np.array(self.light))
        self.plot_glance.set_xdata(np.arange(len(self.glance)))
        self.plot_glance.set_ydata(np.array(self.glance))
        
        self.canvas.draw()
    
    def on_pause_button(self, event):
        self.paused = not self.paused

    def on_calibrate_button(self, event):
        self.calibrate = True
    
    def on_update_pause_button(self, event):
        label = "Resume" if self.paused else "Pause"
        self.pause_button.SetLabel(label)
    
    def on_cb_grid(self, event):
        self.draw_plot()
    
    def on_cb_xlab(self, event):
        self.draw_plot()
    
    def on_save_plot(self, event):
        file_choices = "PNG (*.png)|*.png"
        
        dlg = wx.FileDialog(
            self, 
            message="Save plot as...",
            defaultDir=os.getcwd(),
            defaultFile="plot.png",
            wildcard=file_choices,
            style=wx.SAVE)
        
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.canvas.print_figure(path, dpi=self.dpi)
            self.flash_status_message("Saved to %s" % path)
        

#Start from here *********
    def on_save_data(self, event):
        self.paused = True
        time = range(0,len(self.IR1))
        output(time, self.IR1, self.blink, self.light, self.glance)
        self.paused = False


        
    def on_redraw_timer(self, event):
        # if paused do not add data, but still redraw the plot
        # (to respond to scale modifications, grid change, etc.)
        #
        if not self.paused:
            self.dataAppend = self.datagen.next()
            IR1Append = self.dataAppend[0]
            LightAppend = self.dataAppend[3]
            self.IR1.append(IR1Append)
            print len(self.IR1);
            #Running average of previous three light values
            if self.safe == True:
                if self.avg3Idx < 3:
                    self.avg3 = self.avg3 + self.light[-1]
                    self.avg3Idx = self.avg3Idx + 1
                    self.safe == True
                elif self.avg3Idx == 3:
                    self.avg3_cur = (self.avg3 + self.light[-1])/3.0
                    self.avg3Idx = 1
                    self.avg3 = 0
                    self.safe == True

                #If the current light value is greater than +- 1 from the avg
                if (LightAppend > self.avg3_cur + 2) or (LightAppend < self.avg3_cur - 2):
                    self.glance.append(250)
                else:
                    self.glance.append(180)
            else:
                self.glance.append(180)
                    
                
            #Now add the current light value
            self.light.append(LightAppend)
            
            
            #If we calibrate, average 10 data points
            if self.calibrate:
                #If we're recalibrating, reset the average to 0
                if self.calibrateIdx == 1:
                    self.average = 0
                if self.calibrateIdx < 10:
                    self.average = self.average + IR1Append
                    self.calibrateIdx = self.calibrateIdx + 1
                else:
                    self.average = self.average/10.0
                    self.calibrate = False
                    self.calibrateIdx = 1
                #While calibrating blink will be 0
                self.blink.append(0)
                self.safe = True
            else:
                #If IR1 is twice the calibrated baseline, it's likely a blink
                if IR1Append > self.average + 1000:
                    blinkData = self.average + 1000
                else:
                    blinkData = self.average
                self.blink.append(blinkData)                   
                
        self.draw_plot()
    
    def on_exit(self, event):
        self.Destroy()
    
    def flash_status_message(self, msg, flash_len_ms=1500):
        self.statusbar.SetStatusText(msg)
        self.timeroff = wx.Timer(self)
        self.Bind(
            wx.EVT_TIMER, 
            self.on_flash_status_off, 
            self.timeroff)
        self.timeroff.Start(flash_len_ms, oneShot=True)
    
    def on_flash_status_off(self, event):
        self.statusbar.SetStatusText('')


if __name__ == '__main__':
    
    app = wx.PySimpleApp()
    app.frame = GraphFrame()
    app.frame.Show()
    app.MainLoop()

