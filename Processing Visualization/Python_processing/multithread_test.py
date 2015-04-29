#!/usr/bin/env python

from random import randrange
import wx
import wx.lib.scrolledpanel

# imports added by GreenAsJade
import time
import threading
from wx.lib.pubsub import setupkwargs
from wx.lib.pubsub import pub

class GUI(wx.Frame):

    def __init__(self, parent, id, title):
        screenWidth = 800
        screenHeight = 450
        screenSize = (screenWidth, screenHeight)
        wx.Frame.__init__(self, None, id, title, size=screenSize)
        self.locationFont = locationFont = wx.Font(15, wx.MODERN, wx.NORMAL, wx.BOLD)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer = sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel = panel = wx.lib.scrolledpanel.ScrolledPanel(self, -1, style=wx.SIMPLE_BORDER)
        panel.SetupScrolling()
        panel.SetBackgroundColour('#FFFFFF')
        panel.SetSizer(sizer)
        mainSizer.Add(panel, 15, wx.EXPAND|wx.ALL)
        self.SetSizer(mainSizer)

        pub.subscribe(self.OnNewLabels, "NEW_LABELS")


    def OnNewLabels(self, labels):
        k = 0
        locations = labels
        print locations
        for i in locations:
            sPanels = 'sPanel'+str(k)
            sPanels = wx.Panel(self.panel)
            label = str(k+1)
            print "doing", label
            text = wx.StaticText(sPanels, -1, label)
            text.SetFont(self.locationFont)
            text.SetForegroundColour('#0101DF')
            self.sizer.Add(sPanels, 0, wx.ALL, 5)
            self.sizer.Add(wx.StaticLine(self.panel), 0, wx.ALL|wx.EXPAND, 0)
            k += 1
        self.sizer.Layout()


###############################
#
#

def InterfaceThread(id, log):
    label_generator = Labels()
    while True:
        labels = label_generator.getLabel()   # get the info from the server
        # Tell the GUI about them
        wx.CallAfter(pub.sendMessage, "NEW_LABELS", labels = labels)
        # Tell the logger about them
        wx.CallAfter(log.AppendText, "Sent %s \n" % str(labels))
        time.sleep(5)


class ServerInterface(wx.Frame):

    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, None, id, title)
        self.log = wx.TextCtrl(self, style = wx.TE_MULTILINE)
        interface_thread = threading.Thread(target = InterfaceThread, args = (1, self.log)) 
        interface_thread.start()



################################################
class Labels():
    def getLabel(self):
        mylist =[]
        i = 4 #randrange(10)
        for k in range(1,i+1):
            mylist.append(k)
        return mylist
###############################################

if __name__=='__main__':
    app = wx.App()
    frame = GUI(parent=None, id=-1, title="Test")
    frame.Show()
    server_interface = ServerInterface(parent = None, id=-1, title="Server Log")
    server_interface.Show()
    app.MainLoop()
