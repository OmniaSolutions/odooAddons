'''
Created on Dec 6, 2017

@author: daniel
'''


from OdooQtUi.RPC.rpc import connectionObj
import time
import sys
import random

workcenterLossReasons = {'mancanza_materiale': False,
                         'malfunzionamento': False}


def createWCLoss(connectionObj):
    for workcenterLossReason in workcenterLossReasons.keys():
        res = connectionObj.search('mrp.workcenter.productivity.loss', [('name', '=', workcenterLossReason)])
        if res:
            workcenterLossReasons[workcenterLossReason] = res[0]
        else:
            workcenterLossReasons[workcenterLossReason] = connectionObj.create('mrp.workcenter.productivity.loss', {'name': workcenterLossReason,
                                                                                                                    'manual': True})


def startMachine(workcenterId, workOrderId, nOfTotalPices=1, nOfPicesForCicle=1, nOfError=0):
    error1 = {'id_loss_reason': workcenterLossReasons['mancanza_materiale'],
              'description': 'Mancanza Materiale'}
    error2 = {'id_loss_reason': workcenterLossReasons['malfunzionamento'],
              'description': 'Malfunzionamento'
              }
    nOfLoop = int(nOfTotalPices / nOfPicesForCicle)
    operations = []
    for i in range(nOfLoop):
        operations.append(nOfPicesForCicle)
        if nOfError > 0:
            if random.random() > 0.5:
                operations.append(error1)
            else:
                operations.append(error2)
            nOfError = nOfError - 1
    while nOfError > 0:
        if random.random() > 0.5:
            operations.append(error1)
        else:
            operations.append(error2)
        nOfError = nOfError - 1

    while operations and len(operations) > 0:
        res = connectionObj.read('mrp.workcenter', ['working_state'], workcenterId)
        go = True
        for elem in res:
            if elem.get('working_state', '') == 'blocked':
                print 'Errors! Fix Me in Odoo!'
                go = False
                break
        if go:
            operation = operations.pop(0)
            connectionObj.callCustomMethod('mrp.workorder', 'clientMachineRecordProduction', [workOrderId, operation])
        time.sleep(0.5)


def testWc():
    WcName = raw_input("Name of WorkCenter (levigatura)") or "levigatura"
    WoName = raw_input("Name of the WorkOrder (levigatura)") or "levigatura"
    WcError = raw_input("number of rundom errors (3)") or "3"
    numberCircle = raw_input("number of cycle (10)") or "10"
    interaction = raw_input("number of item x cicle (2)") or "2"
    wcid = 0
    for wc in connectionObj.search('mrp.workcenter', [('name', '=', WcName)]):
        wcid = wc
        break
    woid = 0
    for wc in connectionObj.search('mrp.workorder', [('name', '=', WoName),
                                                     ('workcenter_id', '=', wcid),
                                                     ('date_finished', '=', False)]):
        woid = wc
        break
    startMachine(wcid, woid, int(numberCircle), int(interaction), int(WcError))


def start():
    def connect():
        server_name = raw_input("Server Name (localhost)") or "localhost"
        port = raw_input("Port (8069)") or "8069"
        user = raw_input("user (admin)") or "admin"
        password = raw_input("password (admin)") or "admin"
        database = raw_input("database (rdssubfornitura)") or "rdssubfornitura"
        connectionObj.initConnection('xmlrpc', user, password, database, port, 'http', server_name)
        connectionObj.loginWithUser()
    connect()
    createWCLoss(connectionObj)
    check = ''
    while 1:
        if check == 'out':
            sys.exit()
        check = raw_input("Give me a command: [out or go] (go)") or "go"
        if check == 'go':
            testWc()


if __name__ == '__main__':
    start()
