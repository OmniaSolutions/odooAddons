
##############################################################################
#
#    OmniaSolutions, Your own solutions
#    Copyright (C) 03/ott/2012 OmniaSolutions (<http://www.omniasolutions.eu>). All Rights Reserved
#    info@omniasolutions.eu
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
'''
Created on 03/ott/2012
@author: mboscolo
'''
import os
import sys
import glob
import subprocess


def getPyFileName(uiFile):
    fromUiFileName = os.path.basename(uiFile).split('.')[0]
    fromUiFileName = "ui_" + fromUiFileName + ".py"
    return os.path.join(os.path.dirname(uiFile), fromUiFileName)


srcPath = os.path.join(os.path.dirname(__file__), "*.ui")


for fromFile in glob.glob(srcPath):
    toFile = getPyFileName(fromFile)
    if not os.path.exists(fromFile):
        print "File %s dose not exsist" % fromFile
        continue
    if sys.platform.find('linux') > 0 or ('linux' in sys.platform) > 0:
        cmd = r'python /usr/lib/python2.7/dist-packages/PyQt4/uic/pyuic.py -o %s %s' % (toFile, fromFile)
    else:
        cmd = r'pyuic4 -o %s  %s' % (toFile, fromFile)
        #  seems that subprocess dose not finds the python side package dir
        cmd = r'C:\Python27\Lib\site-packages\PyQt4\pyuic4.bat -o %s %s' % (toFile, fromFile)
    print "Execute", cmd
    try:
        subprocess.call(cmd)
    except:
        os.popen(cmd)
