import traceback
import os

from gevent import getcurrent

def dbg(msg):
    print("<pid:{0},greenlet:{1}>dbg:{2}".format(os.getpid(), id(getcurrent()), msg))
    
dbg('tools.py')

def print_exception_info():
    traceback.print_exc()
