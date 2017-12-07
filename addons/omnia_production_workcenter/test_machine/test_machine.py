'''
Created on Dec 6, 2017

@author: daniel
'''


from OdooQtUi.RPC.rpc import connectionObj
import time

connectionObj.initConnection('xmlrpc', 'admin', 'admin', 'all_11_enterprise', '8069', 'http', '192.168.99.16')
connectionObj.loginWithUser()

workcenterLossReasons = {'mancanza_materiale': False,
                         'malfunzionamento': False}
for workcenterLossReason in workcenterLossReasons.keys():
    res = connectionObj.search('mrp.workcenter.productivity.loss', [('name', '=', workcenterLossReason)])
    if res:
        workcenterLossReasons[workcenterLossReason] = res[0]
    else:
        workcenterLossReasons[workcenterLossReason] = connectionObj.create('mrp.workcenter.productivity.loss', {
                                                                        'name': workcenterLossReason,
                                                                        'manual': True,
                                                                        })

workcenterId = 1
workOrderId = 46
operations = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
              {'id_loss_reason': workcenterLossReasons['mancanza_materiale'],
               'description': 'Mancanza Materiale'
               },
              1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
              1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
              {'id_loss_reason': workcenterLossReasons['malfunzionamento'],
               'description': 'Malfunzionamento'
               },
              1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
              1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
              1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]


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
    
print 'END'