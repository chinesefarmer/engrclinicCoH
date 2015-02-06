import cmd
import subprocess
import shlex
"""
def runCamera():
	class HelloWorld(cmd.Cmd):
	Simple command processor example.
    
    	def do_greet(self, line):
       		print "hello"
    
   		def do_EOF(self, line):
        	return True
"""
if __name__ == '__main__':
	command_line = 'vlc.exe -I rc dshow:// :dshow-vdev="Logitech HD Webcam C615" :dshow-caching=200 :dshow-size=1280x720 :dshow-aspect-ratio=16\:9 :dshow-fps=30 --sout="#duplicate{dst=display,dst='transcode{vcodec=h264,vb=1260,fps=30,size=1280x720}:std{access=file,mux=mp4,dst=C:\\Users\\jyang\\Desktop}'}"'
	args = shlex.split(command_line)
	print args
	p = subprocess.Popen(args)