
from OdooQtUi.RPC.rpc import connectionObj
from PyQt4 import QtGui
from PyQt4 import QtCore
from ui_spesometro.ui_main_window import Ui_MainWindow
from OdooQtUi.interface.login import LoginDialComplete
from generateXml import GenerateXml
import sys
import os
import json

DEFAULT_DATE_FORMAT = '%m/%d/%Y'
DEFAULT_TIME_FORMAT = '%H:%M:%S'


class MainWindow(QtGui.QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.initFields()
        self.loadFromFile()
        self.setStyleWidgets()
        self.setEvents()

    def initFields(self):
        self.odooJournals = []
        self.journalFields = ['code', 'type', 'name']
        self.activeLanguage = 'en_US'
        self.loginFileName = 'login.db'
        self.journalFileName = 'journal.db'
        self.currentDir = os.getcwd()
        self.loginFile = os.path.join(self.currentDir, self.loginFileName)
        self.journalFile = os.path.join(self.currentDir, self.journalFileName)

    def setStyleWidgets(self):
        pass

    def setEvents(self):
        # Dock widgets
        self.pushButton_login.clicked.connect(self.login)
        self.pushButton_settings.clicked.connect(self.setSettings)
        self.pushButton_spesometro.clicked.connect(self.setSpesometro)
        # Other widgets
        self.pushButton_ok.clicked.connect(self.acceptMW)
        self.pushButton_cancel.clicked.connect(self.rejectMW)
        self.pushButton_apply_journals.clicked.connect(self.saveJournals)
        self.pushButton_download.clicked.connect(self.downloadFile)
        self.pushButton_generate_xml.clicked.connect(self.generateXml)

    def acceptMW(self):
        self.close()

    def rejectMW(self):
        self.close()

    def downloadFile(self):
        pass

    def generateXml(self):
        date_from = self.dateEdit_from.dateTime().toPyDateTime().strftime(DEFAULT_DATE_FORMAT)
        date_to = self.dateEdit_to.dateTime().toPyDateTime().strftime(DEFAULT_DATE_FORMAT)
        selectedJournals = self.getSelectedJournals()
        xmlGeneratorObj = GenerateXml(date_from, date_to, selectedJournals)
        xmlGeneratorObj.startReading()

    def getSelectedJournals(self):
        #FIXME: da implementare la ricerca dei sezionali selezionati
        return self.odooJournals

    def setSettings(self):
        self.stackedWidget.setCurrentIndex(1)
        self.loadJournals()

    def writeToFile(self, filePath, toWrite):
        with open(filePath, 'wb') as fileObj:
            fileObj.write(json.dumps(toWrite))
        
    def readFromFile(self, filePath):
        if os.path.exists(filePath):
            with open(filePath, 'rb') as fileObj:
                fileContent = json.loads(fileObj.read())
                return fileContent
        return False
        
    def loadStoredJournals(self):
        odooJournals = self.readFromFile(self.journalFile)
        self.loadJournals(odooJournals)

    def loadLoginSettings(self):
        loginList = self.readFromFile(self.loginFile)
        if loginList:
            self.userName = loginList[0]
            self.userPassword = loginList[1]
            self.databaseName = loginList[2]
            self.xmlrpcPort = loginList[3]
            self.scheme = loginList[4]
            self.xmlrpcServerIP = loginList[5]
            self.connectionType = loginList[6]
            connectionObj.initConnection(self.connectionType, self.userName, self.userPassword, self.databaseName, self.xmlrpcPort, self.scheme, self.xmlrpcServerIP)
            connectionObj.loginWithUser()

    def saveJournals(self):
        self.writeToFile(self.journalFile, self.odooJournals)

    def saveLogin(self):
        self.writeToFile(self.loginFile, connectionObj.getLoginInfos())

    def loadFromFile(self):
        self.loadLoginSettings()
        self.loadStoredJournals()
        
    def setSpesometro(self):
        self.stackedWidget.setCurrentIndex(0)

    def login(self):
        self.loginWithDial()

    def loginWithDial(self):
        loginDialInst = LoginDialComplete()
        loginDialInst.interfaceDial.exec_()
        if connectionObj.userLogged:
            self.saveLogin()
            self.activeLanguage = connectionObj.contextUser.get('lang', 'en_US')
            return True
        return False 

    def checkLogged(self, forceLogin=False):
        logged = connectionObj.userLogged
        if not logged:
            if forceLogin:
                self.loginWithDial()
                return connectionObj.userLogged
        else:
            return True
        return False
        
    def loadJournals(self, journals=[]):
        if self.checkLogged(True) and not self.odooJournals:
            journalIds = connectionObj.search('account.journal', [])
            if not journals:
                self.odooJournals = connectionObj.read('account.journal', self.journalFields, journalIds)
            else:
                self.odooJournals = journals
            for journalDict in self.odooJournals:
                code = journalDict.get('code', '')
                journalType = journalDict.get('type', '')
                name = journalDict.get('name', '')
                obj_id = journalDict.get('id', '')
                rowIndex = self.addLineToSezionaliTable(code, name, journalType, obj_id)
                journalDict['row_index'] = rowIndex
            self.tableWidget.resizeColumnsToContents()
        
    def addLineToSezionaliTable(self, code, name, journalType, objId):
        
        def setItemReadonly(item):
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            
        rowCount = self.tableWidget.rowCount()
        self.tableWidget.setRowCount(rowCount + 1)
        outCodeWidgetItem = QtGui.QTableWidgetItem('')
        outCodeWidgetItem.setFlags(QtCore.Qt.ItemIsUserCheckable |
                                   QtCore.Qt.ItemIsEnabled |
                                   QtCore.Qt.ItemIsEditable)
        outCodeWidgetItem.setCheckState(QtCore.Qt.Unchecked)
        codeItem = QtGui.QTableWidgetItem(code)
        nameItem = QtGui.QTableWidgetItem(name)
        journalItem = QtGui.QTableWidgetItem(journalType)
        obj_id = QtGui.QTableWidgetItem(unicode(objId))
        setItemReadonly(codeItem)
        setItemReadonly(nameItem)
        setItemReadonly(journalItem)
        setItemReadonly(obj_id)
        self.tableWidget.setItem(rowCount, 0, outCodeWidgetItem)
        self.tableWidget.setItem(rowCount, 1, codeItem)
        self.tableWidget.setItem(rowCount, 2, nameItem)
        self.tableWidget.setItem(rowCount, 3, journalItem)
        self.tableWidget.setItem(rowCount, 4, obj_id)
        return rowCount
        
    def center(self):
        frameGm = self.frameGeometry()
        screen = QtGui.QApplication.desktop().screenNumber(QtGui.QApplication.desktop().cursor().pos())
        centerPoint = QtGui.QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    mainW = MainWindow()
    mainW.resize(1200, 800)
    mainW.center()
    mainW.show()
    app.exec_()
