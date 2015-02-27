import cmd
import subprocess
import shlex
import wx
import IMU_Write_Working

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

		MsgBtn = wx.Button(self, label="Send Message")
		MsgBtn.Bind(wx.EVT_BUTTON, self.OnMsgBtn )

		Sizer = wx.BoxSizer(wx.VERTICAL)
		Sizer.Add(startBtn, 0, wx.ALIGN_CENTER|wx.ALL, 5)
		Sizer.Add(MsgBtn, 0, wx.ALIGN_CENTER|wx.ALL, 5)

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
class BlinkPanel(wx.Panel):
	"""This panel holds the plotting of the Blink data"""

	#----------------------------------------------------------------------
	def __init__(self, parent):
		"""Constructor"""
		wx.Panel.__init__(self, parent)

		self.parent = parent  # Sometimes one can use inline Comments

		StopBtn = wx.Button(self, label="Stop BlinkSensor")
		StopBtn.Bind(wx.EVT_BUTTON, self.stopBlink )

		MsgBtn = wx.Button(self, label="Send Message")
		MsgBtn.Bind(wx.EVT_BUTTON, self.OnMsgBtn )

		Sizer = wx.BoxSizer(wx.VERTICAL)
		Sizer.Add(StopBtn, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
		Sizer.Add(MsgBtn, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

		self.SetSizerAndFit(Sizer)

	def stopBlink(self, event=None):
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
		CameraStopBtn.Bind(wx.EVT_BUTTON, self.OnMsgBtn )

		Sizer = wx.BoxSizer(wx.VERTICAL)
		Sizer.Add(CameraStartBtn, 0, wx.ALIGN_CENTER|wx.ALL, 5)
		Sizer.Add(CameraStopBtn, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		self.SetSizerAndFit(Sizer)
	def onStart(self, event=None):
		runCamera(False)

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

		#resize them
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(self.Panel1, 0, wx.ALIGN_CENTER|wx.ALL, 5)
		sizer.AddSpacer(5,5)
		sizer.Add(self.Panel2, 0, wx.ALIGN_CENTER|wx.ALL, 5)
		sizer.AddSpacer(5,5)
		sizer.Add(self.Panel3, 0, wx.ALIGN_CENTER|wx.ALL, 5)

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

		
################################################################################
def runCamera(saving=True):
	stream = 'vlc.exe -I rc dshow:// :dshow-vdev="Logitech HD Webcam C615" :dshow-caching=200 :dshow-size=1280x720 :dshow-aspect-ratio=16\:9 :dshow-fps=30'
	save='--sout= \"#duplicate{dst=display,dst=\'transcode{vcodec=h264,vb=1260,fps=30,size=1280x720}:std{access=file,mux=mp4,dst=C:\\\Users\\\jyang\\\Desktop\\\TestLog_mp4.mp4}\'}\"'
	if saving:
	 save = save
	else:
		save = ''
	command_line = stream + save
	#print command_line
	args = shlex.split(command_line)
	print args
	p = subprocess.Popen(args)
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
	#runCamera()
	buildGUI()