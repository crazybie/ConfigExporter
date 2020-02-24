import time, thread, sys, os, random
from win32gui import *

class WindowsBalloonTip:
    def __init__(self):
        self.msgs = []
        
        wc = WNDCLASS()
        wc.lpszClassName = "PythonTaskbar%s" % random.randrange(0,9999)
        wndClass = RegisterClass(wc)        
        self.hwnd = CreateWindow(wndClass, "Taskbar", 0, 0, 0, 0, 0, 0, 0, None, None)
        
        def loop():
            while True:
                while self.msgs:
                    self.ShowWindow(*self.msgs.pop(0))
                time.sleep(1)
        thread.start_new_thread(loop, ())
        
    def ShowTip(self, title, msg, delay=5):
        self.msgs.append([title, msg, delay])
        
    def ShowWindow(self, title, msg, delay):
        Shell_NotifyIcon(NIM_ADD, (self.hwnd, 0, NIF_ICON | NIF_MESSAGE | NIF_TIP, 0, None, "tooltip"))        
        Shell_NotifyIcon(NIM_MODIFY, (self.hwnd, 0, NIF_INFO, 0, None, "Balloon  tooltip", msg, 0, title))        
        time.sleep(delay)
        Shell_NotifyIcon(NIM_DELETE, (self.hwnd, 0))        
        
        
wbt = WindowsBalloonTip()
title = os.path.basename(sys.argv[0])
def tip(msg, *a):
    wbt.ShowTip(title, msg%a)
    
if __name__=='__main__':
    for i in xrange(10):
        tip('test %s'%i)
    raw_input('done')