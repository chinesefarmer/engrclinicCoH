import cmd
import subprocess
import shlex
import wx

# def readCommands():
# 	class HelloWorld(cmd.Cmd):
# 	Simple command processor example.
    
#     	def do_greet(self, line):
#        		print "hello"
    
#    		def do_EOF(self, line):
#         	return True

def runCamera():
	stream = 'vlc.exe -I rc dshow:// :dshow-vdev="Logitech HD Webcam C615" :dshow-caching=200 :dshow-size=1280x720 :dshow-aspect-ratio=16\:9 :dshow-fps=30'
	save='--sout= \"#duplicate{dst=display,dst=\'transcode{vcodec=h264,vb=1260,fps=30,size=1280x720}:std{access=file,mux=mp4,dst=C:\\\Users\\\jyang\\\Desktop\\\TestLog_mp4.mp4}\'}\"'
	command_line = stream + save
	#print command_line
	args = shlex.split(command_line)
	print args
	p = subprocess.Popen(args)
	return 1

def buildGUI():
	app = wx.App(False)
	#frame = wx.Frame(None, wx.ID_ANY, "HelloWorld")
	#frame.Show(True)
	frame = MainWindow(None, "editor")
	#frame = MyFrame(None, 'Small editor')
	app.MainLoop()

class MyFrame(wx.Frame):
    """ We simply derive a new class of Frame. """
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(200,100))
        self.control = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        self.Show(True)

class MainWindow(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self,parent, title=title, size=(200,100))
        # initialize menu bar
        self.control = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        self.CreateStatusBar() # A Statusbar in the bottom of the window
        # Setting up the menu.
        filemenu= wx.Menu()

        # wx.ID_ABOUT and wx.ID_EXIT are standard IDs provided by wxWidgets.
        filemenu.Append(wx.ID_ABOUT, "&About"," Information about this program")
        filemenu.AppendSeparator()
        filemenu.Append(wx.ID_EXIT,"E&xit"," Terminate the program")

        # Creating the menubar.
        menuBar = wx.MenuBar()
        menuBar.Append(filemenu,"&File") # Adding the "filemenu" to the MenuBar
        self.SetMenuBar(menuBar)  # Adding the MenuBar to the Frame content.
  
        #Add a butoon
        menuItem = filemenu.Append(wx.ID_ABOUT, "&About"," Information about this program")
        self.Bind(wx.EVT_MENU, self.OnAbout, menuItem)




        self.Show(True)

	def OnButtonClick(self, event):
    	self.running == False


if __name__ == '__main__':
	#runCamera()
	buildGUI()