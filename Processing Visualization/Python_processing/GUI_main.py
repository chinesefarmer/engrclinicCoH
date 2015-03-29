import cmd
import subprocess
import shlex
import time
import wx
import time
#Import IMU module
import IMU_Write_Working

# The recommended way to use wx with mpl is with the WXAgg
# backend. 
#
# inherited from nicole's code
#from datetime import *
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar
import numpy as np
import pylab

#Data comes from here
from FallSiteVisit_GUI import SerialData
import outputnumbers

################################################################################
#Data input processor
def IRdataGen(isSerial=False): # Default to dummy variables
	if(~isSerial):
		IR1 = outputnumbers.genNums(1, 104)
		IR2 = outputnumbers.genNums(1, 104)
		IR3 = outputnumbers.genNums(1, 104)
		light= 0
		return [IR1, IR2, IR3, light]
	else:
		return SerialData()


################################################################################

#Data comes from here
# Gui_main.py
# This is the main 
# def readCommands():
# 	class HelloWorld(cmd.Cmd):
# 	Simple command processor example.
	
#     	def do_greet(self, line):
#        		print "hello"
	
#    		def do_EOF(self, line):
#         	return True


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
		IMU_Write_Working.IMU_write()


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

		CameraStartBtn = wx.Button(self, label="Start Stream")
		CameraStartBtn.Bind(wx.EVT_BUTTON, self.onStart )

		CameraStopBtn = wx.Button(self, label="Stop Stream")
		CameraStopBtn.Bind(wx.EVT_BUTTON, self.stopCamera)


		Sizer = wx.BoxSizer(wx.VERTICAL)
		Sizer.Add(CameraStartBtn, 0, wx.ALIGN_CENTER|wx.ALL, 5)
		Sizer.Add(CameraStopBtn, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		self.SetSizerAndFit(Sizer)
	def onStart(self, event=None):
		runCamera(True)

    def stopCamera(self, event = None):
        quitCamera()


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

################################################################################
class MainFrame(wx.Frame):
	def __init__(self, parent, title):
		wx.Frame.__init__(self,parent, title=title, size=(300,400))
		# initialize menu bar
		self.CreateStatusBar() # A Statusbar in the bottom of the window

		#add widgets
		self.Panel1 = IMUPanel(self)
		self.Panel2 = BlinkPanel(self)
		self.Panel3 = CameraPanel(self)
		#self.graphBlink = GraphPanel(self)

		#resize them
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(self.Panel1, 0, wx.ALIGN_CENTER|wx.ALL, 5)
		sizer.AddSpacer(5,5)
		sizer.Add(self.Panel2, 0, wx.ALIGN_CENTER|wx.ALL, 5)
		sizer.AddSpacer(5,5)
		sizer.Add(self.Panel3, 0, wx.ALIGN_CENTER|wx.ALL, 5)
		#sizer.Add(self.graphBlink, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		self.SetSizerAndFit(sizer)
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

	def onQuit(self, event=None):
		"""Exit"""
		self.Close()
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

		MsgBtn = wx.Button(self, label="Show Live Plot")
		MsgBtn.Bind(wx.EVT_BUTTON, self.OnMsgBtn )

		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(StopBtn, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
		sizer.Add(MsgBtn, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

		sizer2 = wx.BoxSizer(wx.VERTICAL)
		self.SetSizerAndFit(Sizer)

	def stopBlink(self, event=None):
		"""Do nothing."""
		pass

	def OnMsgBtn(self, event=None):
		"""Bring up the live plotting."""
  	


class GraphPanel(wx.Frame):
    """ The graphing frames frame of the application
    """
    title = 'Demo: dynamic matplotlib graph'
    
    def __init__(self, parent):
    
	    
	    #**************************
	    #Remember, this comes in the form [IR1, IR2, IR3, light]
	    #self.datagen = IRdataGen()
	    #self.data = self.datagen.next()
	    self.data = IRdataGen()
	    #**************************
	    self.time = [datetime.now().time()]
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
	    
	    #self.create_menu()
	    #self.create_status_bar()
	   	#self.create_main_panel()
	    
	    self.redraw_timer = wx.Timer(self)
	    self.Bind(wx.EVT_TIMER, self.on_redraw_timer, self.redraw_timer)        
	    self.redraw_timer.Start(REFRESH_INTERVAL_MS)

    def create_menu(self):
        savePlotBtn =  wx.Button(self, "Save plot to file")
        savePlotBtn.Bind(wx.EVT_BUTTON, self.on_save_plot)
        menu_file.AppendSeparator()
        m_save = menu_file.Append(-1, "Save data")
        self.Bind(wx.EVT_MENU, self.on_save_data, m_save)


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

    def init_plot(self, ):
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
		
################################################################################
#def camera():
#	def __init__(self, parent):
#		self.p = subprocess.Popen() 
# vlc.exe -I rc dshow:// :dshow-vdev="Logitech HD Webcam C615" :dshow-caching=200 :dshow-size=1280x720 :dshow-aspect-ratio=16\:9 :dshow-fps=30 --sout="#duplicate{dst=display,dst='transcode{vcodec=h264,vb=1260,fps=30,size=1280x720}:std{access=file,mux=mp4,dst=C:\\Users\\jyang\\Desktop\\designReview-2.mp4}'}"
def runCamera(saving=False):
	stream = 'vlc.exe -I rc dshow:// :dshow-vdev="Logitech HD Webcam C615" :dshow-caching=200 :dshow-size=1280x720 :dshow-aspect-ratio=16\:9 :dshow-fps=30'

	save=' --sout=\"#duplicate{dst=display,dst=\'transcode{vcodec=h264,vb=1260,fps=30,size=1280x720}:std{access=file,mux=mp4,dst=C:\\\Users\\\jyang\\\Desktop\\\TestLog_mp4.mp4}\'}\"'

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
