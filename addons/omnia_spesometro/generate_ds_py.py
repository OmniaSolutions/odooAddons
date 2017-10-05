import os
import sys
import glob
import subprocess


def getPyFileName(uiFile):
    fromUiFileName = os.path.basename(uiFile).split('.')[0]
    fromUiFileName = fromUiFileName + ".py"
    return os.path.join(os.path.dirname(uiFile), fromUiFileName)

def getPyFileNameSubs(uiFile):
    fromUiFileName = os.path.basename(uiFile).split('.')[0]
    fromUiFileName = fromUiFileName + "_subs.py"
    return os.path.join(os.path.dirname(uiFile), fromUiFileName)

def removePresentFile(filePath):
    if os.path.exists(filePath):
        os.unlink(filePath)
    
srcPath = os.path.join(os.path.dirname(__file__), "agenzia_entrate.xsd")


for fromFile in glob.glob(srcPath):
    toFile = getPyFileName(fromFile)
    if not os.path.exists(fromFile):
        print "File %s dose not exsist" % fromFile
        continue
    tofileSubs = getPyFileNameSubs(fromFile)
    removePresentFile(toFile)
    removePresentFile(tofileSubs)
    cmd = r'python generateDS.py -o %s -s %s %s' % (toFile, tofileSubs, fromFile)
    if sys.platform.find('linux') > 0 or ('linux' in sys.platform) > 0:
        cmd = r'generateDS.py -o %s -s %s %s' % (toFile, tofileSubs, fromFile)
#         cmd = r'python generateDS.py -o %s -s %s' % (toFile, fromFile)
#     else:
#         cmd = r'pyuic4 -o %s  %s' % (toFile, fromFile)
#         #  seems that subprocess dose not finds the python side package dir
#         cmd = r'C:\Python27\Lib\site-packages\PyQt4\pyuic4.bat -o %s %s' % (toFile, fromFile)
    print "Execute", cmd
    try:
        subprocess.call(cmd)
    except Exception, ex:
        os.popen(cmd)

