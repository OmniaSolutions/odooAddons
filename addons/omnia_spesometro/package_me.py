'''
Created on Oct 10, 2017

@author: daniel
'''

import subprocess
import os
import OdooQtUi

cmd = "pyinstaller start.py -p %s --onefile" % (OdooQtUi.__path__[0])
# Remove --onefile to have all files displayed

print "Execute", cmd
try:
    subprocess.call(cmd)
except Exception, ex:
    os.popen(cmd)