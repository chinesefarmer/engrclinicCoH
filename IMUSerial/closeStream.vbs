set shell = CreateObject("WScript.Shell")
WScript.Sleep 1400
shell.SendKeys"~stop~"
Wscript.Sleep 2400
shell.SendKeys"^c"