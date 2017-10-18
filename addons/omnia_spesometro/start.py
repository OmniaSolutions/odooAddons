
from OdooQtUi.RPC.rpc import connectionObj
from OdooQtUi.utils_odoo_conn import constants
from OdooQtUi.utils_odoo_conn import utils
from PyQt4 import QtGui
from PyQt4 import QtCore
from ui_spesometro.ui_main_window import Ui_MainWindow
from OdooQtUi.interface.login import LoginDialComplete
from generateXml import GenerateXml
from datetime import datetime
import sys
import os
import pickle

DEFAULT_DATE_FORMAT = '%m/%d/%Y'
DEFAULT_TIME_FORMAT = '%H:%M:%S'
JOURNAL_TYPES = ['sale', 'sale_refund', 'purchase', 'purchase_refund']
ACCOUNT_TAX_TYPES = ['name', 'description', 'type_tax_use', 'amount']


class MainWindow(QtGui.QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.initFields()
        self.loadFromFile()
        self.setStyleWidgets()
        self.setEvents()
        self.setSpesometro()

    def initFields(self):
        self.journalFields = ['code', 'type', 'name']
        self.activeLanguage = 'en_US'
        self.loginFileName = 'login.db'
        self.journalFileName = 'journal.db'
        self.imposteFileName = 'imposte.db'
        self.rowItemRel = {}    # Used to save and read journal in settings
        self.accountTaxes = []  # Used to save and read account taxes
        self.currentDir = os.getcwd()
        self.loginFile = os.path.join(self.currentDir, self.loginFileName)
        self.journalFile = os.path.join(self.currentDir, self.journalFileName)
        self.imposteFile = os.path.join(self.currentDir, self.imposteFileName)
        
        starting_day_of_current_year = datetime.now().date().replace(month=1, day=1)    
        ending_day_of_current_year = datetime.now().date().replace(month=12, day=31)
        self.dateEdit_from.setDate(QtCore.QDate(starting_day_of_current_year.year, starting_day_of_current_year.month, starting_day_of_current_year.day))
        self.dateEdit_to.setDate(QtCore.QDate(ending_day_of_current_year.year, ending_day_of_current_year.month, ending_day_of_current_year.day))
        
        self.dockWidget_2.setFeatures(QtGui.QDockWidget.DockWidgetFloatable | QtGui.QDockWidget.DockWidgetMovable)

    def setStyleWidgets(self):
        self.setStyleSheet(constants.VIOLET_BACKGROUND)
        self.pushButton_generate_xml.setStyleSheet(constants.LOGIN_ACCEPT_BUTTON + 'font-size: 24px;')
        commonButtonStyle = constants.BUTTON_COMMON + constants.BACKGROUND_LIGHT_BLUE + constants.BOLD_FONT + 'color:black;'
        self.pushButton_login.setStyleSheet(commonButtonStyle)
        self.pushButton_spesometro.setStyleSheet(commonButtonStyle)
        self.pushButton_settings.setStyleSheet(commonButtonStyle)
        self.pushButton_ok.setText('Exit')
        self.pushButton_ok.setStyleSheet(constants.LOGIN_ACCEPT_BUTTON + 'font-size: 15px;')
        self.tableWidget.setStyleSheet(constants.TABLE_LIST_LIST)
        self.tableWidget_imposte.setStyleSheet(constants.TABLE_LIST_LIST)
        self.label_date_from.setStyleSheet(constants.LOGIN_LABEL)
        self.label_date_to.setStyleSheet(constants.LOGIN_LABEL)
        self.label_out_file_name.setStyleSheet(constants.LOGIN_LABEL)
        self.label_sezionali.setStyleSheet(constants.LOGIN_LABEL)
        self.dateEdit_from.setStyleSheet(constants.DATE_STYLE)
        self.dateEdit_to.setStyleSheet(constants.DATE_STYLE)
        self.lineEdit_out_file_name.setStyleSheet(constants.LOGIN_LINEEDIT_STYLE)
        self.widget_content.setStyleSheet(constants.BACKGROUND_WHITE)
        self.dockWidget_2.setStyleSheet(constants.BACKGROUND_WHITE)
        self.pushButton_apply_journals.setStyleSheet(constants.BUTTON_STYLE)
        self.pushButton_open_path.setStyleSheet(constants.BUTTON_STYLE)
        self.label_progress.setStyleSheet(constants.LOGIN_LABEL)
        self.tableWidget_imposte.resizeColumnsToContents()
        self.pushButton_help_imposte.setStyleSheet(constants.LOGIN_ACCEPT_BUTTON)
        self.pushButton_help_journal.setStyleSheet(constants.LOGIN_ACCEPT_BUTTON)
        self.textEdit_imposte.setHidden(True)
        self.textEdit_journal.setHidden(True)

    def setEvents(self):
        # Dock widgets
        self.pushButton_login.clicked.connect(self.login)
        self.pushButton_settings.clicked.connect(self.setSettings)
        self.pushButton_spesometro.clicked.connect(self.setSpesometro)
        # Other widgets
        self.pushButton_ok.clicked.connect(self.acceptMW)
        self.pushButton_apply_journals.clicked.connect(self.saveJournals)
        self.pushButton_generate_xml.clicked.connect(self.generateXml)
        self.pushButton_open_path.clicked.connect(self.openPath)
        
        self.pushButton_help_imposte.clicked.connect(self.expandHideImposteHelp)
        self.pushButton_help_journal.clicked.connect(self.expandHideJournalHelp)

    def expandHideImposteHelp(self):
        if not self.textEdit_imposte.isVisible():
            self.textEdit_imposte.setHidden(False)
        else:
            self.textEdit_imposte.setHidden(True)
    
    def expandHideJournalHelp(self):
        if not self.textEdit_journal.isVisible():
            self.textEdit_journal.setHidden(False)
        else:
            self.textEdit_journal.setHidden(True)

    def acceptMW(self):
        if utils.launchMessage('Are you sure you want to quit?', 'question'):
            self.close()

    def openPath(self):
        newSavePath = utils.getDirectoryFromSystem(parent=None, pathToOpen='')
        self.lineEdit_out_file_name.setText(newSavePath)
        
    def generateXml(self):
        date_from = self.dateEdit_from.dateTime().toPyDateTime().strftime(DEFAULT_DATE_FORMAT)
        date_to = self.dateEdit_to.dateTime().toPyDateTime().strftime(DEFAULT_DATE_FORMAT)
        selectedJournals = self.getSelectedJournals()
        savingPath = unicode(self.lineEdit_out_file_name.text())
        xmlGeneratorObj = GenerateXml(date_from, date_to, selectedJournals, self.progressBar, self.label_progress, self.accountTaxes, savingPath)
        xmlGeneratorObj.startReading()
        utils.launchMessage('End to generate XML files.', msgType='info')

    def getSelectedJournals(self):
        checkedJournals = []
        for pyObjectJournal in self.rowItemRel.values():
            if pyObjectJournal.checked:
                checkedJournals.append(pyObjectJournal)
        return checkedJournals

    def setSettings(self):
        self.stackedWidget.setCurrentIndex(1)
        self.loadJournals()
        self.loadImposte()

    def writeToFile(self, filePath, toWrite):
        with open(filePath, 'wb') as fileObj:
            fileObj.write(pickle.dumps(toWrite))
        
    def readFromFile(self, filePath):
        if os.path.exists(filePath):
            with open(filePath, 'rb') as fileObj:
                fileContent = pickle.loads(fileObj.read())
                return fileContent
        return False

    def loadStoredImposte(self):
        odooImposte = self.readFromFile(self.imposteFile)
        self.loadImposte(odooImposte)
 
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
        self.writeToFile(self.journalFile, self.rowItemRel)
        self.writeToFile(self.imposteFile, self.accountTaxes)
        utils.launchMessage('Tutti i cambiamenti sono stati salvati', 'info')

    def saveLogin(self):
        self.writeToFile(self.loginFile, connectionObj.getLoginInfos())

    def loadFromFile(self):
        self.loadLoginSettings()
        self.loadStoredJournals()
        self.loadStoredImposte()
        
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

    def loadImposte(self, account_taxes=[]):
        if self.checkLogged(True):
            if not account_taxes:
                taxIds = connectionObj.search('account.tax', [])
                odooImposte = connectionObj.read('account.tax', ACCOUNT_TAX_TYPES, taxIds)
                for impostaDict in odooImposte:
                    odooName = impostaDict.get('name', '')
                    odooDesc = impostaDict.get('description', '')
                    odooTypeTax = impostaDict.get('type_tax_use', '')
                    odooAmount = impostaDict.get('amount', 0)
                    odooId = impostaDict.get('id', 0)
                    self.addLineToImposteTable(odooName, odooDesc, odooTypeTax, odooAmount, odooId, '', '', '', '')
            else:
                for pyObject in account_taxes:
                    self.addLineToImposteTable(pyObject.odooName,
                                                            pyObject.odooDesc,
                                                            pyObject.odooTypeTax,
                                                            pyObject.odooAmount,
                                                            pyObject.odooId,
                                                            pyObject.natura,
                                                            pyObject.detraibile,
                                                            pyObject.deducibile,
                                                            pyObject.esigibilitaIVA
                                                            )
            self.tableWidget_imposte.resizeColumnsToContents()
    
    def loadJournals(self, journals={}):
        if self.checkLogged(True) and not self.rowItemRel:
            if not journals:
                journalIds = connectionObj.search('account.journal', [('type', 'in', JOURNAL_TYPES)])
                odooJournals = connectionObj.read('account.journal', self.journalFields, journalIds)
                for journalDict in odooJournals:
                    code = journalDict.get('code', '')
                    journalType = journalDict.get('type', '')
                    name = journalDict.get('name', '')
                    obj_id = journalDict.get('id', '')
                    rowIndex = self.addLineToSezionaliTable('', code, name, journalType, obj_id, False)
                    journalDict['row_index'] = rowIndex
            else:
                self.rowItemRel = journals
                for pyObject in self.rowItemRel.values():
                    rowIndex = self.addLineToSezionaliTable(pyObject.code,
                                                            pyObject.odooCode,
                                                            pyObject.odooName,
                                                            pyObject.journalType,
                                                            pyObject.odooID,
                                                            pyObject.checked
                                                            )

            self.tableWidget.resizeColumnsToContents()

    def addLineToImposteTable(self, odooName, odooDesc, odooTypeTax, odooAmount, odooId, natura, detraibile, deducibile, esigibilitaIVA):
        def setItemReadonly(item):
            item.setFlags(QtCore.Qt.ItemIsEnabled)
        
        def setItemEditable(item):
            item.setFlags(QtCore.Qt.ItemIsEnabled |
                          QtCore.Qt.ItemIsEditable)
            
        rowCount = self.tableWidget_imposte.rowCount()
        self.tableWidget_imposte.setRowCount(rowCount + 1)
        
        tableRowObj = classTableRow()
        odooNameItem = QtGui.QTableWidgetItem(odooName)
        odooDescItem = QtGui.QTableWidgetItem(odooDesc)
        odooTypeTaxItem = QtGui.QTableWidgetItem(odooTypeTax)
        odooAmountItem = QtGui.QTableWidgetItem(unicode(odooAmount))
        odooIdItem = QtGui.QTableWidgetItem(unicode(odooId))
        naturaItem = QtGui.QTableWidgetItem(natura)
        detraibileItem = QtGui.QTableWidgetItem(detraibile)
        deducibileItem = QtGui.QTableWidgetItem(deducibile)
        esigibilitaIVAItem = QtGui.QTableWidgetItem(esigibilitaIVA)
        
        setItemReadonly(odooNameItem)
        setItemReadonly(odooDescItem)
        setItemReadonly(odooTypeTaxItem)
        setItemReadonly(odooAmountItem)
        setItemReadonly(odooIdItem)
        
        self.tableWidget_imposte.setItem(rowCount, 0, odooNameItem)
        self.tableWidget_imposte.setItem(rowCount, 1, odooDescItem)
        self.tableWidget_imposte.setItem(rowCount, 2, odooTypeTaxItem)
        self.tableWidget_imposte.setItem(rowCount, 3, odooAmountItem)
        self.tableWidget_imposte.setItem(rowCount, 4, odooIdItem)
        self.tableWidget_imposte.setItem(rowCount, 5, naturaItem)
        self.tableWidget_imposte.setItem(rowCount, 6, detraibileItem)
        self.tableWidget_imposte.setItem(rowCount, 7, deducibileItem)
        self.tableWidget_imposte.setItem(rowCount, 8, esigibilitaIVAItem)
        
        tableRowObj.odooName = odooName
        tableRowObj.odooDesc = odooDesc
        tableRowObj.odooTypeTax = odooTypeTax
        tableRowObj.odooAmount = odooAmount
        tableRowObj.odooId = odooId
        tableRowObj.natura = natura
        tableRowObj.detraibile = detraibile
        tableRowObj.deducibile = deducibile
        tableRowObj.esigibilitaIVA = esigibilitaIVA
        tableRowObj.rowIndex = rowCount
        
        self.accountTaxes.append(tableRowObj)
        
        self.tableWidget_imposte.itemChanged.connect(self.impostaChanged)

    def impostaChanged(self, item):
        rowIndex = item.row()
        colIndex = item.column()
        value = unicode(item.text())
        for impostaObj in self.accountTaxes:
            if impostaObj.rowIndex == rowIndex:
                if colIndex == 5:   # Natura
                    impostaObj.natura = value
                elif colIndex == 6:   # Detraibile
                    impostaObj.detraibile = value
                elif colIndex == 7:   # Deducibile
                    impostaObj.deducibile = value
                elif colIndex == 8:   # Esigibilita IVA
                    impostaObj.esigibilitaIVA = value
                break
        
    def addLineToSezionaliTable(self, code, odooCode, name, journalType, objId, checked=False):
        
        def setItemReadonly(item):
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            
        rowCount = self.tableWidget.rowCount()
        self.tableWidget.setRowCount(rowCount + 1)
        outCodeWidgetItem = QtGui.QTableWidgetItem(code)
        outCodeWidgetItem.setFlags(QtCore.Qt.ItemIsUserCheckable |
                                   QtCore.Qt.ItemIsEnabled |
                                   QtCore.Qt.ItemIsEditable)
        tableRowObj = classTableRow()
        if not checked:
            outCodeWidgetItem.setCheckState(QtCore.Qt.Unchecked)
            tableRowObj.checked = False
        else:
            outCodeWidgetItem.setCheckState(QtCore.Qt.Checked)
            tableRowObj.checked = True
        codeItem = QtGui.QTableWidgetItem(odooCode)
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
        
        self.tableWidget.itemClicked.connect(self.handleItemClicked)
        self.tableWidget.itemChanged.connect(self.cellChanged)
        tableRowObj.code = code
        tableRowObj.odooCode = odooCode
        tableRowObj.odooName = name
        tableRowObj.journalType = journalType
        tableRowObj.odooID = objId
        self.rowItemRel[rowCount] = tableRowObj
        return rowCount

    def cellChanged(self, item):
        rowIndex = item.row()
        colIndex = item.column()
        value = unicode(item.text())
        pyObject = self.rowItemRel.get(rowIndex, None)
        if colIndex == 0 and pyObject:
            pyObject.code = value
        
    def handleItemClicked(self, item):
        rowIndex = item.row()
        if item.checkState() == QtCore.Qt.Checked:
            self.rowItemRel[rowIndex].checked = True
        else:
            self.rowItemRel[rowIndex].checked = False

    def center(self):
        frameGm = self.frameGeometry()
        screen = QtGui.QApplication.desktop().screenNumber(QtGui.QApplication.desktop().cursor().pos())
        centerPoint = QtGui.QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())


class classTableRow(object):
    
    def __init__(self):
        self.code = ''
        self.odooCode = ''
        self.odooName = ''
        self.journalType = ''
        self.odooID = ''
        self.checked = False
    
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    mainW = MainWindow()
    mainW.resize(1300, 800)
    mainW.center()
    mainW.show()
    app.exec_()
