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

		self.displayPanel1 = GraphPanel3x(self, source=self.data, index = [self.smoothRindex, self.smoothPindex, self.smoothYindex], timerSource = self.redraw_timer, title = "RPY data vs Time", xAxisLabel = "Time (s)", yAxisLabel = "Smooth RPY")
		sizerDisplayV2.Add(self.displayPanel1, 1, wx.EXPAND|wx.ALL)
		self.displayPanelBlink = GraphPanel(self, source=self.data, index = self.blinkIndex, timerSource = self.redraw_timer, title = "Blink Sensor data vs Time", xAxisLabel = "Time (s)", yAxisLabel ="Blink")
		sizerDisplayV1.Add(self.displayPanelBlink, 1, wx.EXPAND|wx.ALL)
		
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
		self.blinkIndex = 7
		self.pitchIndex = 6
		self.smoothRindex = 4 
		self.smoothPindex = 3
		self.smoothYindex = 2

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
					self.displayPanelBlink.data=self.data
					self.displayPanel1.data = self.data
					#print "senddata", self.data
					self.displayPanelBlink.refresh()
					self.displayPanel1.refresh()
					#self.displayPanelBlink.redraw_timer = self.redraw_timer
					#self.displayPanel1.redraw_timer = self.redraw_timer
			except KeyboardInterrupt:
				pass

	def stopAll(self, event=None):
		"""stop or start all plots"""
		self.paused = False if self.paused else True
		self.gotData = False
		label = "Resume all Sensors" if (~self.paused) else "Pause all Sensors"

		self.displayPanel1.paused = False if self.displayPanel1.paused else True
		#label = "Resume" if (~self.displayPanel1.paused) else "Pause"
		#self.displayPanel1.pause_button.SetLabel(label)

		self.displayPanelBlink.paused = False if self.displayPanelBlink.paused else True
		#label = "Resume" if (~self.displayPanelBlink.paused) else "Pause"
		#self.displayPanelBlink.pause_button.SetLabel(label)
		pass

	def saveAll(self, event=None):
		"""Save all the data"""
		self.s.end()

	def onQuit(self, event=None):
		"""Exit"""
		self.Close()

################################################################################
class GraphPanel3x(wx.Panel):
	""" The graphing frames frame of the application
	"""
	
	def __init__(self, parent, source, index = 0, timerSource = None , title = "Display Data", xAxisLabel = "x axis", yAxisLabel = "y axis"):
		wx.Panel.__init__(self,parent)
		
		#**************************
		#Remember, this comes in the form [sensor1, sensor2, sensor3]
		self.index = index
		self.data = source
		#**************************
		self.time = [datetime.datetime.now().time()]
		self.sensorIndex1, self.sensorIndex2, self.sensorIndex3 = index
		self.sensorVal1 = [self.data[self.sensorIndex1]]
		self.sensorVal2 = [self.data[self.sensorIndex2]]
		self.sensorVal3 = [self.data[self.sensorIndex3]]
		self.xmin = 0
		self.xmax = 50
		self.ymax = 100
		self.ymin = -100
		#print "sensorValues", self.sensorVal1, self.sensorVal2, self.sensorVal3
		self.title = title
		self.xAxisLabel = xAxisLabel
		self.yAxisLabel = yAxisLabel

		self.safe = False
		self.paused = False
		self.calibrate = True
		self.calibrateIdx = 1
		self.avg3Idx = 1
		
		self.create_main_panel()
		
		self.redraw_timer = timerSource
		#self.redraw_timer = wx.Timer(self)
		#self.Bind(wx.EVT_TIMER, self.on_redraw_timer, self.redraw_timer)        
		#self.redraw_timer.Start(1) #refresh rate in ms

	def create_main_panel(self):
		self.panel = wx.Panel(self)

		self.init_plot()
		
		self.canvas = FigCanvas(self, -1, self.fig)
		self.xmin_control = BoundControlBox(self, -1, "X min", 0, True)
		self.xwinSize_control = BoundControlBox(self, -1, "X windowSize", 50, True)
		#comment this out
		self.ymin_control = BoundControlBox(self, -1, "Y min", 0, True)
		self.ymax_control = BoundControlBox(self, -1, "Y max", 100, True)

		#self.pause_button = wx.Button(self, -1, "Pause")
		#self.Bind(wx.EVT_BUTTON, self.on_pause_button, self.pause_button)
		#self.Bind(wx.EVT_UPDATE_UI, self.on_update_pause_button, self.pause_button)

		self.hbox1 = wx.BoxSizer(wx.HORIZONTAL)
		#self.hbox1.Add(self.pause_button, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)

		self.hbox2 = wx.BoxSizer(wx.HORIZONTAL)
		self.hbox2.Add(self.xmin_control, border=5, flag=wx.ALL)
		self.hbox2.Add(self.xwinSize_control, border=5, flag=wx.ALL)
		self.hbox2.AddSpacer(24)
		self.hbox2.Add(self.ymin_control, border=5, flag=wx.ALL)
		self.hbox2.Add(self.ymax_control, border=5, flag=wx.ALL)
		
		self.vbox = wx.BoxSizer(wx.VERTICAL)
		self.vbox.Add(self.canvas, 1, flag=wx.LEFT | wx.TOP | wx.GROW)        
		self.vbox.Add(self.hbox2, 0, flag=wx.ALIGN_LEFT | wx.TOP)
		self.vbox.Add(self.hbox1, 0, flag=wx.ALIGN_LEFT | wx.TOP)
		
		self.SetSizer(self.vbox)
		self.vbox.Fit(self)

	def init_plot(self):
		self.dpi = 100
		self.fig = Figure((3.0, 3.0), dpi=self.dpi)

	
		self.axes_sensor= self.fig.add_subplot(111)
		self.axes_sensor.set_axis_bgcolor('black')
		self.axes_sensor.set_title(self.title, size=12)

		self.axes_sensor.set_xlabel(self.xAxisLabel, size = 8)
		self.axes_sensor.set_ylabel(self.yAxisLabel, size = 8)

		pl.setp(self.axes_sensor.get_xticklabels(), fontsize=8)
		pl.setp(self.axes_sensor.get_yticklabels(), fontsize=8)
		#pl.setp(self.axes_sensor.get_yticklabels(), visible= False)
		#pl.setp(self.axes_sensor2.get_xticklabels(), fontsize=8)
		#pl.setp(self.axes_sensor2.get_yticklabels(), fontsize=8)

		# plot the data as a line series, and save the reference 
		# to the plotted line series
		#
		print "init", self.data
		#White = sensor
		self.plot_sensor1 = self.axes_sensor.plot(
			self.sensorVal1, 
			linewidth=1,
			color='white')[0]

		self.plot_sensor2 = self.axes_sensor.plot(
			self.sensorVal2, 
			linewidth=1,
			color='blue')[0]

		self.plot_sensor3 = self.axes_sensor.plot(
			self.sensorVal3, 
			linewidth=1,
			color='green')[0]
			
	def draw_plot(self):
		""" Redraws the plot
		"""

		xmin = self.xmin
		xmax = self.xmax
		ymin = self.ymin
		ymax = self.ymax
		# when xmin is on auto, it "follows" xmax to produce a 
		# sliding window effect. therefore, xmin is assigned after
		# xmax.
		# comment this out
		xmax = len(self.sensorVal1) if len(self.sensorVal1) > 50 else 50
			
		if self.xmin_control.is_auto():            
			xmin = xmax - int(self.xwinSize_control.manual_value())
		else:
			xmin = int(self.xmin_control.manual_value())


		# for ymin and ymax, find the minimal and maximal values
		# in the data set and add a mininal margin.
		# 
		# note that it's easy to change this scheme to the 
		# minimal/maximal value in the current display, and not
		# the whole data set.
		# 
		# if self.ymin_control.is_auto():
		# 	ymin = round(min(self.sensorVal1), 0) - 1
		# else:
		# 	ymin = int(self.ymin_control.manual_value())
		
		# if self.ymax_control.is_auto():
		# 	ymax = round(max(self.sensorVal1), 0) + 1
		# else:
		# 	ymax = int(self.ymax_control.manual_value())

		self.axes_sensor.set_xbound(lower=xmin, upper=xmax)
		self.axes_sensor.set_ybound(lower=ymin, upper=ymax)
		#pl.setp(self.axes_sensor.get_yticklabels(), visible= False)
		# Using setp here is convenient, because get_xticklabels
		# returns a list over which one needs to explicitly 
		# iterate, and setp already handles this.
		#  
		#pl.setp(self.axes_sensor1.get_xticklabels(), 
		#	visible=self.cb_xlab.IsChecked())
		self.plot_sensor1.set_xdata(np.arange(len(self.sensorVal1)))
		self.plot_sensor1.set_ydata(np.array(self.sensorVal1))
		self.plot_sensor2.set_xdata(np.arange(len(self.sensorVal2)))
		self.plot_sensor2.set_ydata(np.array(self.sensorVal2))
		self.plot_sensor3.set_xdata(np.arange(len(self.sensorVal3)))
		self.plot_sensor3.set_ydata(np.array(self.sensorVal3))
		self.canvas.draw()	
			

	def on_redraw_timer(self, event):
		# if paused do not add data, but still redraw the plot
		# (to respond to scale modifications, grid change, etc.)
		if not self.paused:
			try:	
				#self.data = self.datagen.next()
				#print "recieved data", self.data
				sensorAppend1 = self.data[self.sensorIndex1]
				sensorAppend2 = self.data[self.sensorIndex2]
				sensorAppend3 = self.data[self.sensorIndex3]
				self.sensorVal1.append(sensorAppend1)
				self.sensorVal2.append(sensorAppend2)
				self.sensorVal3.append(sensorAppend3)
				#print "sensorValues", self.sensorVal1, self.sensorVal2, self.sensorVal3
				self.time.append(datetime.datetime.now().time())
				self.draw_plot()
			except KeyboardInterrupt:
				pass
	def refresh(self):
		if not self.paused:
			try:	
				#self.data = self.datagen.next()
				#print "recieved data", self.data
				sensorAppend1 = self.data[self.sensorIndex1]
				sensorAppend2 = self.data[self.sensorIndex2]
				sensorAppend3 = self.data[self.sensorIndex3]
				self.sensorVal1.append(sensorAppend1)
				self.sensorVal2.append(sensorAppend2)
				self.sensorVal3.append(sensorAppend3)
				#print "sensorValues", self.sensorVal1, self.sensorVal2, self.sensorVal3
				self.time.append(datetime.datetime.now().time())
				self.draw_plot()
			except KeyboardInterrupt:
				pass

################################################################################
class GraphPanel(wx.Panel):
	""" The graphing frames frame of the application
	"""
	
	def __init__(self, parent, source, index = 0, timerSource = [datetime.datetime.now().time()] , title = "Display Data", xAxisLabel = "x axis", yAxisLabel = "y axis"):
		wx.Panel.__init__(self,parent)
		
		#**************************
		self.index = index
		self.data = source
		#**************************
		self.time = [datetime.datetime.now().time()]
		self.sensorVal = [self.data[index]]
		self.xmin = 0
		self.xmax = 50
		self.ymax = 15
		self.ymin = 0

		self.title = title
		self.xAxisLabel = xAxisLabel
		self.yAxisLabel = yAxisLabel

		self.safe = False
		self.paused = False
		self.calibrate = True
		self.calibrateIdx = 1
		self.avg3Idx = 1
		
		self.create_main_panel()
		
		self.redraw_timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.on_redraw_timer, self.redraw_timer)        
		self.redraw_timer.Start(1) #refresh rate in ms

	def create_menu(self):
		savePlotBtn =  wx.Button(self, label="Save plot to file")
		savePlotBtn.Bind(wx.EVT_BUTTON, self.on_save_plot)
		menu_file.AppendSeparator()
		m_save = menu_file.Append(-1, label="Save data")
		self.Bind(wx.EVT_MENU, self.on_save_data, m_save)


	def create_main_panel(self):
		self.panel = wx.Panel(self)

		self.init_plot()
		
		self.canvas = FigCanvas(self, -1, self.fig)
		self.xmin_control = BoundControlBox(self, -1, "X min", 0, True)
		self.xmax_control = BoundControlBox(self, -1, "X max", 50, True)
		self.ymin_control = BoundControlBox(self, -1, "Y min", 0, True)
		self.ymax_control = BoundControlBox(self, -1, "Y max", 100, True)

		#self.pause_button = wx.Button(self, -1, "Pause")
		#self.Bind(wx.EVT_BUTTON, self.on_pause_button, self.pause_button)
		#self.Bind(wx.EVT_UPDATE_UI, self.on_update_pause_button, self.pause_button)

		self.hbox1 = wx.BoxSizer(wx.HORIZONTAL)
		#self.hbox1.Add(self.pause_button, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)

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
		
		self.SetSizer(self.vbox)
		self.vbox.Fit(self)

	def create_status_bar(self):
		self.statusbar = self.CreateStatusBar()

	def init_plot(self):
		self.dpi = 100
		self.fig = Figure((3.0, 3.0), dpi=self.dpi)

		self.axes_sensor1= self.fig.add_subplot(111)
		self.axes_sensor1.set_axis_bgcolor('black')
		self.axes_sensor1.set_title(self.title, size=12)

		self.axes_sensor1.set_xlabel(self.xAxisLabel, size = 8)
		self.axes_sensor1.set_ylabel(self.yAxisLabel, size = 8)

		pl.setp(self.axes_sensor1.get_yticklabels(), fontsize=8)
		# plot the data as a line series, and save the reference 
		# to the plotted line series
		#
		print "init", self.data
		#White = sensor
		self.plot_sensor1 = self.axes_sensor1.plot(
			self.sensorVal, 
			linewidth=1,
			color='white')[0]

	def draw_plot(self):
		""" Redraws the plot
		"""
		xmin = self.xmin
		xmax = self.xmax
		ymin = self.ymin
		ymax = self.ymax
		# when xmin is on auto, it "follows" xmax to produce a 
		# sliding window effect. therefore, xmin is assigned after
		# xmax.
		#
		if self.xmax_control.is_auto():
			xmax = len(self.sensorVal) if len(self.sensorVal) > 50 else 50
		else:
			xmax = int(self.xmax_control.manual_value())
			
		if self.xmin_control.is_auto():            
			xmin = xmax - 50
		else:
			xmin = int(self.xmin_control.manual_value())

		self.axes_sensor1.set_xbound(lower=xmin, upper=xmax)
		self.axes_sensor1.set_ybound(lower=ymin, upper=ymax)

		self.plot_sensor1.set_xdata(np.arange(len(self.sensorVal)))
		self.plot_sensor1.set_ydata(np.array(self.sensorVal))

		self.canvas.draw()	

	def on_redraw_timer(self, event):
		# if paused do not add data, but still redraw the plot
		# (to respond to scale modifications, grid change, etc.)
		if not self.paused:
			try:	
				if(self.data[0] != 1):
					pass
				else:
					sensorAppend = self.data[self.index]
					#print "recieved Data", sensorAppend
					self.sensorVal.append(sensorAppend)
					self.time.append(datetime.datetime.now().time())
					self.draw_plot()
			except KeyboardInterrupt:
				pass
	def refresh(self):
		if not self.paused:
			try:	
				if(self.data[0] != 1):
					pass
				else:
					sensorAppend = self.data[self.index]
					#print "recieved Data", sensorAppend
					self.sensorVal.append(sensorAppend)
					self.time.append(datetime.datetime.now().time())
					self.draw_plot()
			except KeyboardInterrupt:
				pass

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
def buildGUI():
	app = wx.App(False)
	#frame = wx.Frame(None, wx.ID_ANY, "HelloWorld")
	#frame.Show(True)
	frame = MainFrame(None, "Sensor Control Interface")
	#frame = MyFrame(None, 'Small editor')
	print "hi"
	app.MainLoop()

if __name__ == '__main__':
	buildGUI()