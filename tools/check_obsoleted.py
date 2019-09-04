'''
Created on 9 Jun 2016

@author: dsmerghetto
'''
COMMIT = True
import os
import datetime
import tempfile
from DbWrapper.wrapperOpenERP import BaseDbIntegration
BaseDbIntegration.newStyleCall = True
BaseDbIntegration.create('admin', 'admin', 'tomorrow', 'localhost', '8069', '', 'http')
limit = None
objDicts = BaseDbIntegration.GetDetailsSearch('product.product', [[('id', '>', -1)]], ['engineering_code', 'engineering_revision', 'state'], limit=limit)

result = {}

logFile = os.path.join(tempfile.gettempdir(), 'fix_obsoleted_%s.txt' % (datetime.datetime.now()))
outFileLog = open(logFile, 'w')


def printAndLog(msg):
    '''
        Eventualmente abilitare il log per file  e abilitare le scritture in questa funzione al posto degli append
        E chiudere i file alla fine di tutto
    '''
    outFileLog.write(str(msg) + '\n')
    print (msg)

objects = len(objDicts)
printAndLog('compute %r items' % (objects))

for dictObj in objDicts:
    engineering_code = dictObj.get('engineering_code', '')
    engineering_revision = dictObj.get('engineering_revision', 0)
    obj_id = dictObj.get('id', 0)
    state = dictObj.get('state', '')
    
    if engineering_code not in result:
        result[engineering_code] = {}
    if engineering_revision not in result[engineering_code]:
        result[engineering_code][engineering_revision] = dictObj

printAndLog('Parse result')

errors = []
to_eval = len(result)
count = 0
for eng_code, vals in result.items():
    if count % 40 == 0:
        printAndLog('Evaluate %r / %r' % (count, to_eval))
    keys = vals.keys()
    keys.sort()
    last_rev = vals[keys[-1]]
    state = last_rev['state']
    if state in ['obsoleted', 'undermodify']:
        errors.append(last_rev)
        printAndLog('[WARNING] Component %r in state %r' % (last_rev['id'], state))
    count += 1
    
printAndLog('\nFound %r errors\n' % (len(errors)))

for error_vals in errors:
    if COMMIT:
        res_id = error_vals.get('id', False)
        values = {'state': 'released'}
        kArgs = {}
        res = BaseDbIntegration.UpdateValue('product.product', [res_id], values, kArgs)
        if not res:
            printAndLog('Cannot update state for component res_id')
    

printAndLog('End to evaluate components')

printAndLog('Start to evaluate documents\n')


objDicts = BaseDbIntegration.GetDetailsSearch('plm.document', [[('id', '>', -1)]], ['name', 'revision_id', 'state'], limit=limit)

result = {}

objects = len(objDicts)
printAndLog('compute %r items' % (objects))

for dictObj in objDicts:
    engineering_code = dictObj.get('name', '')
    engineering_revision = dictObj.get('revision_id', 0)
    obj_id = dictObj.get('id', 0)
    state = dictObj.get('state', '')
    
    if engineering_code not in result:
        result[engineering_code] = {}
    if engineering_revision not in result[engineering_code]:
        result[engineering_code][engineering_revision] = dictObj

printAndLog('Parse result')

errors = []
to_eval = len(result)
count = 0
for eng_code, vals in result.items():
    if count % 40 == 0:
        printAndLog('Evaluate %r / %r' % (count, to_eval))
    keys = vals.keys()
    keys.sort()
    last_rev = vals[keys[-1]]
    state = last_rev['state']
    if state in ['obsoleted', 'undermodify']:
        errors.append(last_rev)
    count += 1
    
printAndLog('\nFound %r errors\n' % (len(errors)))

for error_vals in errors:
    if COMMIT:
        res_id = error_vals.get('id', False)
        values = {'state': 'released'}
        kArgs = {'check': False}
        try:
            res = BaseDbIntegration.UpdateValue('plm.document', [res_id], values, kArgs)
            if not res:
                printAndLog('Cannot update state for document res_id')
            else:
                printAndLog('[INFO] document %r updated from state %r to released' % (last_rev['id'], state))
        except Exception as ex:
            printAndLog('Cannot update document %r due to error %r' % (res_id, ex))
    

printAndLog('Done')

outFileLog.close()
    
    