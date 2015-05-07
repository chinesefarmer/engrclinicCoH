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

#from datetime import *

 
################################################################################
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

			#Ensures that no errors are in the serialData array
			#serialData[0] == 1 means that there were no failures
			#serialData[0] == 0 means there was at least one failure
			if(self.serialData[0] == 1):
				#[roll, pitch, self.nextY ,currTime, ready]
				IMUData = self.imuSensor.calcRPYData(self.serialData[1])
				# Checks to see if the calibration period has ended
				if(IMUData[4] == 1):
					# processedData = [smoothRoll,smoothPitch,smoothYaw,
					# self.timeAtRoll,self.timeAtPitch,self.timeAtYaw, # THESE ARE 360 length array
					# rollMax,rollFocus, pitchMax ,pitchFocus, yawMax ,yawFocus] # *Max is the focus angle and
																		# *focus is the percent time focusing
					processedData = self.imuSensor.processIMUData(IMUData)

					# Handles the IR Sensor
					try:
						IR1 = float((self.serialData[1])[0])
						numRecentBlinks = self.blinkSensor.Algorithm(IR1, False)
						#if(numRecentBlinks != 0):
						
						if(numRecentBlinks != 0):
							self.prevBlinks = numRecentBlinks
							print numRecentBlinks
							outputData = [1,1] + processedData[0:5] + [numRecentBlinks]
						else:
							outputData = [1,1] + processedData[0:5] + [self.prevBlinks]

						#print "output withIR"
					except ValueError:
						outputData = [1,1] + processedData[0:5] + [0]
						print "Value Error"

					# Slows down the cycle enough to prevent divide by zero errors
					tm.sleep(.001)
				else:
					#print "imu data not ready"
					outputData =  [0,0] + [0,0,0,0,0,0]
			else:
				print "no sensor data"	
				outputData =  [0,0] + [0,0,0,0,0,0]
			#print "my outputs???", outputData
			return outputData
		#Run only at the end of the op  
		except KeyboardInterrupt:
			self.end()
			

	def end(self):
		self.usb.close()
		self.blinkSensor.saveFile()

		pass
		


################################################################################
class MainFrame(wx.Frame):
	def __init__(self, parent, title):
		wx.Frame.__init__(self,parent, title=title, size=(300,400))
		# initialize menu bar
		self.CreateStatusBar() # A Statusbar in the bottom of the window
		#resize them
		sizerH = wx.BoxSizer(wx.HORIZONTAL)


		box = wx.StaticBox(self, -1, label = "Control Box")
		
		#init GUI
		sizerV = wx.StaticBoxSizer(box, wx.VERTICAL)


		StopBtn = wx.Button(self, label="Stop All Sensors")
		StopBtn.Bind(wx.EVT_BUTTON, self.stopAll )
		SaveBtn = wx.Button(self, label= "Save All Data")
		SaveBtn.Bind(wx.EVT_BUTTON, self.saveAll)
		#sizerH = wx.BoxSizer(wx.VERTICAL)
		sizerV.Add(StopBtn, 0,wx.ALIGN_CENTER|wx.ALL, 5)
		sizerV.AddSpacer(5,5)
		sizerV.Add(SaveBtn, 0,wx.ALIGN_CENTER|wx.ALL, 5)
		
		#add widgets
		self.Panel1 = IMUPanel(self)
		sizerV.Add(self.Panel1, 0, wx.EXPAND)
		
		"""
		self.Panel2 = BlinkPanel(self)
		sizerV.AddSpacer(5,5)
		sizerV.Add(self.Panel2, 0, wx.EXPAND)
		"""
		self.Panel3 = CameraPanel(self)
		sizerV.AddSpacer(5,5)
		sizerV.Add(self.Panel3, 0, wx.EXPAND)

		sizerDisplayV1 = wx.BoxSizer(wx.VERTICAL)
		sizerDisplayV2 = wx.BoxSizer(wx.VERTICAL)
		# Sensor inputs
		self.s = sensorData()
		self.displayPanel1 = GraphPanel(self, source=self.s, dataType = 2, title = "Roll data vs Time", xAxisLabel = "Time (s)", yAxisLabel = "Smooth Roll")
		sizerDisplayV1.Add(self.displayPanel1, 1, wx.EXPAND|wx.ALL)

		self.displayPanel2 = GraphPanel(self, source=self.s, dataType = 3, title = "Pitch data vs Time", xAxisLabel = "Time (s)", yAxisLabel = "Smooth Pitch")
		sizerDisplayV1.Add(self.displayPanel2, 1, wx.EXPAND|wx.ALL)

		self.displayPanel3 = GraphPanel(self, source=self.s, dataType = 4, title = "Yaw data vs Time", xAxisLabel = "Time (s)", yAxisLabel = "Smooth Yaw")
		sizerDisplayV2.Add(self.displayPanel3, 1, wx.EXPAND|wx.ALL)

		self.displayPanel4 = GraphPanel(self, source=self.s, dataType = 7, title = "Blink Sensor data vs Time", xAxisLabel = "Time (s)", yAxisLabel = "Blink")
		sizerDisplayV2.Add(self.displayPanel4, 1, wx.EXPAND|wx.ALL)
		
		sizerH.Add(sizerDisplayV1, 0, wx.EXPAND)
		sizerH.Add(sizerDisplayV2, 0, wx.EXPAND)
		#self.displayPanel = GraphPanel(self,genIRserialData)
		#self.displayPanel = ColorMapPanel(self)
		
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
		#Add a butoon
		#menuItem = filemenu.Append(wx.ID_ABOUT, "&About"," Information about this program")
		
		self.Show(True)

	def stopAll(self, event=None):
		"""stop or start all plots"""
		self.displayPanel1.paused = False if self.displayPanel1.paused else True
		label = "Resume" if (~self.displayPanel1.paused) else "Pause"
		self.displayPanel1.pause_button.SetLabel(label)

		self.displayPanel2.paused = False if self.displayPanel2.paused else True
		label = "Resume" if (~self.displayPanel1.paused) else "Pause"
		self.displayPanel2.pause_button.SetLabel(label)

		self.displayPanel3.paused = False if self.displayPanel3.paused else True
		label = "Resume" if (~self.displayPanel1.paused) else "Pause"
		self.displayPanel3.pause_button.SetLabel(label)

		self.displayPanel4.paused = False if self.displayPanel4.paused else True
		label = "Resume" if (~self.displayPanel1.paused) else "Pause"
		self.displayPanel4.pause_button.SetLabel(label)

		pass

	def saveAll(self, event=None):
		"""Save all the data"""
		self.s.end()

	def onQuit(self, event=None):
		"""Exit"""
		self.Close()

################################################################################
class IMUPanel(wx.Panel):
	"""This panel holds the plotting of the IMU data"""

	#----------------------------------------------------------------------
	def __init__(self, parent):
		"""Constructor"""
		wx.Panel.__init__(self, parent)

		self.parent = parent  # Sometimes one can use inline Comments

		startBtn = wx.Button(self, label="Run IMU")
		startBtn.Bind(wx.EVT_BUTTON, self.startIMU )

		#Not yet implemented..more butteons!
		#MsgBtn = wx.Button(self, label="Send Message")
		#MsgBtn.Bind(wx.EVT_BUTTON, self.OnMsgBtn )

		Sizer = wx.BoxSizer(wx.VERTICAL)
		Sizer.Add(startBtn, 0, wx.ALIGN_CENTER|wx.ALL, 5)
		#Sizer.Add(MsgBtn, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		self.SetSizerAndFit(Sizer)

	def startIMU(self, event=None):
		"""start IMU"""
		#IMU_Write_Working.IMU_write()
		pass

	def DoNothing(self, event=None):
		"""Do nothing."""
		pass

	def OnMsgBtn(self, event=None):
		"""Bring up a wx.MessageDialog with a useless message."""
		dlg = wx.MessageDialog(self,
							   message='A completely useless message',
							   caption='A Message Box',
							   style=wx.OK|wx.ICON_INFORMATION
							   )
		dlg.ShowModal()
		dlg.Destroy()


	#----------------------------------------------------------------------
	def onShowPopup(self, event):
		""""""
		win = TestPopup(self.GetTopLevelParent(), wx.SIMPLE_BORDER)

		btn = event.GetEventObject()
		pos = btn.ClientToScreen( (0,0) )
		sz =  btn.GetSize()
		win.Position(pos, (0, sz[1]))

		win.Show(True)

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
				
		###

		Sizer = wx.BoxSizer(wx.VERTICAL)
		Sizer.Add(self.CameraStartBtn, 0, wx.ALIGN_CENTER|wx.ALL, 5)
		Sizer.Add(self.CameraStopBtn, 0, wx.ALIGN_CENTER|wx.ALL, 5)
		Sizer.Add(self.textBox)

		self.SetSizerAndFit(Sizer)
	def onStart(self, event=None):
		self.name = self.textBox.GetValue()
		if not self.name:
			dt = datetime.datetime.now()
			name = self.directoryName + dt.strftime("%m_%d_%Y_%H_%M%p")
		else:
			name = self.directoryName
		runCamera(name, saving =True)

	#def getValue(self):



	def closeCamera(self, event=None):
		closeCamera()
		

	def OnMsgBtn(self, event=None):
		"""Bring up a wx.MessageDialog with a useless message."""
		dlg = wx.MessageDialog(self,
							   message='A completely useless message',
							   caption='A Message Box',
							   style=wx.OK|wx.ICON_INFORMATION
							   )
		dlg.ShowModal()
		dlg.Destroy()


###############################################################################
class BlinkPanel(wx.Panel):
	"""This panel holds the plotting of the Blink data"""

	#----------------------------------------------------------------------
	def __init__(self, parent):
		"""Constructor"""
		wx.Panel.__init__(self, parent)

		self.parent = parent  # Sometimes one can use inline Comments

		StopBtn = wx.Button(self, label="Stop Blink Sensor")
		StopBtn.Bind(wx.EVT_BUTTON, self.stopBlink )

		sizerH = wx.BoxSizer(wx.VERTICAL)
		sizerH.Add(StopBtn, 0,wx.ALIGN_CENTER|wx.ALL, 5)
		sizerH.AddSpacer(5,5)
		sizerH.Add(MsgBtn, 0,wx.ALIGN_CENTER|wx.ALL, 5)

		sizer2 = wx.BoxSizer(wx.VERTICAL)
		self.SetSizerAndFit(sizerH)

	def stopBlink(self, event=None):
		"""Do nothing."""
	
		pass

	def OnMsgBtn(self, event=None):
		"""Bring up the live plotting."""
	
###############################################################################

class GraphPanel(wx.Panel):
	""" The graphing frames frame of the application
	"""
	
	def __init__(self, parent, source=sensorData, dataType = 3, title = "Display Data", xAxisLabel = "x axis", yAxisLabel = "y axis"):
		wx.Panel.__init__(self,parent)
		self.dataType = dataType
		#**************************
		#Remember, this comes in the form [sensor, IR2, IR3, light]
		#self.datagen = genIRserialData()
		self.datagen = source
		self.data = self.datagen.next()
		#**************************
		self.time = [datetime.datetime.now().time()]
		self.sensorVal = [self.data[self.dataType]]
		#print self.sensorVal
		#self.sensorVal2 = [self.data[1]]
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

		self.pause_button = wx.Button(self, -1, "Pause")
		self.Bind(wx.EVT_BUTTON, self.on_pause_button, self.pause_button)
		self.Bind(wx.EVT_UPDATE_UI, self.on_update_pause_button, self.pause_button)

		#self.calibrate_button = wx.Button(self, -1, "Calibrate")
		#self.Bind(wx.EVT_BUTTON, self.on_calibrate_button, self.calibrate_button)
		"""
		self.cb_grid = wx.CheckBox(self, -1, 
			"Show Grid",
			style=wx.ALIGN_RIGHT)
		self.Bind(wx.EVT_CHECKBOX, self.on_cb_grid, self.cb_grid)
		self.cb_grid.SetValue(True)
		
		self.cb_xlab = wx.CheckBox(self, -1, 
			"Show X labels",
			style=wx.ALIGN_RIGHT)
		self.Bind(wx.EVT_CHECKBOX, self.on_cb_xlab, self.cb_xlab)        
		self.cb_xlab.SetValue(True)
		"""
		self.hbox1 = wx.BoxSizer(wx.HORIZONTAL)
		self.hbox1.Add(self.pause_button, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
		"""
		self.hbox1.AddSpacer(20)
		self.hbox1.Add(self.calibrate_button, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
		self.hbox1.AddSpacer(20)
		self.hbox1.Add(self.cb_grid, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
		self.hbox1.AddSpacer(10)
		self.hbox1.Add(self.cb_xlab, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
		"""
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
		#self.axes_sensor2 = self.fig.add_subplot(122)
		self.axes_sensor1.set_axis_bgcolor('black')
		#self.axes_sensor2.set_axis_bgcolor('black')
		self.axes_sensor1.set_title(self.title, size=12)
		#self.axes_sensor2.set_title('Head Positioning', size=12)
		
		self.axes_sensor1.set_xlabel(self.xAxisLabel, size = 8)
		self.axes_sensor1.set_ylabel(self.yAxisLabel, size = 8)

		#self.axes_sensor2.set_xlabel("Time (seconds)" , size = 8)
		#self.axes_sensor2.set_ylabel("Percent time focusing on field" , size = 8)

		#self.axes_sensor1.
		pl.setp(self.axes_sensor1.get_xticklabels(), fontsize=8)
		pl.setp(self.axes_sensor1.get_yticklabels(), fontsize=8)
		#pl.setp(self.axes_sensor2.get_xticklabels(), fontsize=8)
		#pl.setp(self.axes_sensor2.get_yticklabels(), fontsize=8)

		# plot the data as a line series, and save the reference 
		# to the plotted line series
		#
		print "init", self.data
		#White = sensor
		self.plot_sensor1 = self.axes_sensor1.plot(
			self.sensorVal, 
			linewidth=1,
			color='white')[0]


		#self.plot_sensor2 = self.axes_sensor2.plot(
		#	self.sensorVal2,
		#	linewidth = 1,
		#	color = 'white')[0]
		
			

	def draw_plot(self):
		""" Redraws the plot
		"""
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


		# for ymin and ymax, find the minimal and maximal values
		# in the data set and add a mininal margin.
		# 
		# note that it's easy to change this scheme to the 
		# minimal/maximal value in the current display, and not
		# the whole data set.
		# 
		if self.ymin_control.is_auto():
			ymin = round(min(self.sensorVal), 0) - 1
		else:
			ymin = int(self.ymin_control.manual_value())
		
		if self.ymax_control.is_auto():
			ymax = round(max(self.sensorVal), 0) + 1
		else:
			ymax = int(self.ymax_control.manual_value())

		self.axes_sensor1.set_xbound(lower=xmin, upper=xmax)
		self.axes_sensor1.set_ybound(lower=ymin, upper=ymax)

		#****Change this later
		#self.axes_sensor2.set_xbound(lower=xmin, upper=xmax)
		#self.axes_sensor2.set_ybound(lower=ymin, upper=ymax)
		#self.axes_sensor2.set_ybound(lower=round(min(min(self.light),min(self.glance)),0)-1,
		#								 upper=round(max(max(self.light),max(self.glance)),0)+1)
		
		# anecdote: axes_sensor1.grid assumes b=True if any other flag is
		# given even if b is set to False.
		# so just passing the flag into the first statement won't
		# work.
		#
		"""
		if self.cb_grid.IsChecked():
			self.axes_sensor1.grid(True, color='gray')
			#self.axes_sensor2.grid(True, color='gray')
		else:
			self.axes_sensor1.grid(False)
			#self.axes_sensor2.grid(False)
		"""
		# Using setp here is convenient, because get_xticklabels
		# returns a list over which one needs to explicitly 
		# iterate, and setp already handles this.
		#  
		#pl.setp(self.axes_sensor1.get_xticklabels(), 
		#	visible=self.cb_xlab.IsChecked())
		
		self.plot_sensor1.set_xdata(np.arange(len(self.sensorVal)))
		self.plot_sensor1.set_ydata(np.array(self.sensorVal))
		#self.plot_sensor2.set_xdata(np.arange(len(self.sensorVal2)))
		#self.plot_sensor2.set_ydata(np.array(self.sensorVal2))

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

	def on_redraw_timer(self, event):
		# if paused do not add data, but still redraw the plot
		# (to respond to scale modifications, grid change, etc.)
		
		if not self.paused:
			try:	
				self.data = self.datagen.next()
				#print "recieved data", self.data
				if(self.data[0] != 1):
					pass
				else:
					#print "self.data", self.data
					#print "place", self.dataType
					sensorAppend = self.data[self.dataType]
					#print "recieved Data", sensorAppend
					#sensor2Append = self.dataAppend[3]
					self.sensorVal.append(sensorAppend)
					self.time.append(datetime.datetime.now().time())
					#self.sensorVal2.append(sensor2Append)
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
#def camera():
#   def __init__(self, parent):
#       self.p = subprocess.Popen() 
# vlc.exe -I rc dshow:// :dshow-vdev="Logitech HD Webcam C615" :dshow-caching=200 :dshow-size=1280x720 :dshow-aspect-ratio=16\:9 :dshow-fps=30 --sout="#duplicate{dst=display,dst='transcode{vcodec=h264,vb=1260,fps=30,size=1280x720}:std{access=file,mux=mp4,dst=C:\\Users\\jyang\\Desktop\\designReview-2.mp4}'}"
def runCamera(name, saving=False):
	stream = 'vlc.exe -I rc dshow:// :dshow-vdev="Logitech HD Webcam C615" :dshow-caching=200 :dshow-size=1280x720 :dshow-aspect-ratio=16\:9 :dshow-fps=30'

	save=' --sout=\"#duplicate{dst=display,dst=\'transcode{vcodec=h264,vb=1260,fps=30,size=1280x720}:std{access=file,mux=mp4,dst=' + 'C:\\\Users\\\ClinicCoH\\\Desktop\\\TestLog_mp4.mp4}\'}\"'#name + '.mp4}\'}\"' #

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
	#frame = wx.Frame(None, wx.ID_ANY, "HelloWorld")
	#frame.Show(True)
	frame = MainFrame(None, "editor")
	#frame = MyFrame(None, 'Small editor')
	app.MainLoop()

if __name__ == '__main__':
	buildGUI()
