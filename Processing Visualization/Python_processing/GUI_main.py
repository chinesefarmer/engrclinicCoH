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
	frame = wx.Frame(None, wx.ID_ANY, "HelloWorld")
	frame.Show(True)
	#app.MainLoop()

if __name__ == '__main__':


	runCamera()
	#buidGui()