'''
Created on 27 Nov 2018

@author: dsmerghetto
'''

"""
Delete wkf_workitem that are not containing related workflow instance

delete from wkf_workitem where id in (
select id from wkf_workitem a where not exists (select id from wkf_instance b where a.inst_id = b.id)
);

delete from ir_model_data where model = 'product.category';
"""

from DbWrapper.wrapperOpenERP import BaseDbIntegration
from prettytable import PrettyTable
import logging
import tempfile
import datetime
import psycopg2
import os

global cur
conn = None
cur = None
USER_NAME = 'admin'
USER_PASS = 'cvmpws1!'
DB_USER = 'odoo'
DB_PASS = 'odoo'
DB_NAME = 'civiemme_real'
SERVER_ADDRESS = '127.0.0.1'
SERVER_PORT = '8069'

COMMIT = False
PSYCOPG = False
test_a_few = 10000000
logFile = os.path.join(tempfile.gettempdir(), 'fix_workflow_%s.txt' % (datetime.datetime.now()))
outFileLog = open(logFile, 'w')

strCommit = raw_input('Do Commit? [true, True, T]')
if strCommit in ('true', 'True', 'T'):
    COMMIT = True

strCommit = raw_input('Use Psycopg? [true, True, T]')
if strCommit in ('true', 'True', 'T'):
    PSYCOPG = True

def printAndLog(msg):
    '''
        Eventualmente abilitare il log per file  e abilitare le scritture in questa funzione al posto degli append
        E chiudere i file alla fine di tutto
    '''
    outFileLog.write(str(msg) + '\n')
    print (msg)


def login():
    printAndLog('Start Login')
    cur = None
    try:
        conn = psycopg2.connect("dbname='%s' user='%s' host='%s' password='%s'" % (DB_NAME, DB_USER, SERVER_ADDRESS, DB_PASS))
        cur = conn.cursor()
        BaseDbIntegration.create(USER_NAME, USER_PASS, DB_NAME, SERVER_ADDRESS, SERVER_PORT, '', 'http')
        if not BaseDbIntegration.isLoggedIn:
            printAndLog('Login Failed')
            return False, cur
        BaseDbIntegration.newStyleCall = False
        return True, cur
    except Exception, ex:
        printAndLog(ex)
    return False, cur


def dictify(headers, rows):
    wkf_list = []
    for row in rows:
        localDict = dict(zip(headers, row))
        for key, val in localDict.items():
            if isinstance(val, (list, tuple)):
                localDict[key] = val[0]
        wkf_list.append(localDict)
    return wkf_list


def getCorrectWorkflow():
    if PSYCOPG:
        cur.execute("""SELECT id, name, osv from wkf;""")
        rows = cur.fetchall()
        wkf_list = dictify(('id', 'name', 'osv'), rows)
    else:
        wkf_list = BaseDbIntegration.GetDetailsSearch('workflow', [], ['id', 'name', 'osv'])
    msg = '''
Select the correct CHOICE number workflow type\n'''
    valueDict = {}
    pp_table = PrettyTable(['CHOICE', 'Object', 'Id', 'Name'])
    for wkf_dict in wkf_list:
        wkf_id = wkf_dict.get('id', '')
        wkf_name = wkf_dict.get('name', '')
        wkf_obj = wkf_dict.get('osv', '')
        index = wkf_list.index(wkf_dict)
        valueDict[str(index)] = {'id': wkf_id, 'name': wkf_name, 'object': wkf_obj}
        pp_table.add_row([index, wkf_obj, wkf_id, wkf_name])
    printAndLog(pp_table)
    res = raw_input(msg)
    if res in valueDict.keys():
        return valueDict.get(res)
    return False


def getWorkflowActivity(wkf_id):
    out = {}
    pp_table = PrettyTable(['ID', 'WKF ID', 'Kind', 'Name', 'Action'])
    if PSYCOPG:
        cur.execute("""SELECT id, wkf_id, kind, name, action from wkf_activity where wkf_id = %s;""" % (wkf_id))
        rows = cur.fetchall()
        wkf_list = dictify(('id', 'wkf_id', 'kind', 'name', 'action'), rows)
    else:
        wkf_list = BaseDbIntegration.GetDetailsSearch('workflow.activity', [('wkf_id', '=', wkf_id)], ['id', 'wkf_id', 'kind', 'name', 'action'])
    for wkf_dict in wkf_list:
        obj_id = wkf_dict.get('id', '')
        wkf_id = wkf_dict.get('wkf_id', '') or ''
        kind = wkf_dict.get('kind', '') or ''
        name = wkf_dict.get('name', '') or ''
        action = wkf_dict.get('action', '') or ''
        pp_table.add_row([obj_id, wkf_id, kind, name, action])
        out[name] = obj_id
    printAndLog(pp_table)
    printAndLog('\n\n')
    return out


def getObjectList(model):
    if PSYCOPG:
        if model == 'product.product':
            cur.execute("""SELECT id, product_tmpl from %s;""" % (model.replace('.', '_')))
        else:
            cur.execute("""SELECT id, state, name from %s;""" % (model.replace('.', '_')))
        rows = cur.fetchall()
        return dictify(('id', 'state', 'name'), rows)
    else:
        return BaseDbIntegration.GetDetailsSearch(model, queryFilter=[], fields=['id', 'state', 'name'], limit=test_a_few)


def getWkfInstance(model, res_id, wkf_id):
    cur.execute("""SELECT id, wkf_id, res_type, state, res_id from wkf_instance where res_id = %s and res_type = '%s' and wkf_id = %s;""" % (res_id, model, wkf_id))
    rows = cur.fetchall()
    wkf_list = dictify(('id', 'wkf_id', 'res_type', 'state', 'res_id'), rows)
#     if PSYCOPG:
#         cur.execute("""SELECT id, wkf_id, res_type, state, res_id from wkf_instance where res_id = %s and res_type = %s and wkf_id = %s;""" % (res_id, model, wkf_id))
#         rows = cur.fetchall()
#         wkf_list = dictify(('id', 'wkf_id', 'res_type', 'state', 'res_id'), rows)
#     else:
#         wkf_list = BaseDbIntegration.GetDetailsSearch('workflow.instance', [('res_id', '=', res_id), ('res_type', '=', model), ('wkf_id', '=', wkf_id)], 
#                                                   ['id', 'wkf_id', 'res_type', 'state', 'res_id'])
    for wkf_dict in wkf_list:
        return wkf_dict
    return {}


def createWkfInstance(model, wkf_id, obj_id):
    uid = 1
    state = 'active'
    infoValue = {
        'res_type': model,
        'uid': uid,
        'wkf_id': wkf_id,
        'res_id': obj_id,
        'state': state,
        }
    printAndLog('[%s] Create Wkf Instance with values %s' % (obj_id, infoValue))
    if COMMIT:
        if PSYCOPG:
            keys = ['res_type', 'uid', 'wkf_id', 'res_id', 'state']
            vals = [model, uid, wkf_id, obj_id, state]
            cur.execute("""INSERT INTO wkf_instance (%s) values (%s);""" % (keys, vals))
            rows = cur.fetchall()
            return rows[0]
        else:
            res = BaseDbIntegration.Create('workflow.instance', infoValue)
        return res
    return -1


def createWkfWorkitem(act_id, inst_id, obj_id):
    state = 'active'
    infoValue = {
        'act_id': act_id,
        'inst_id': inst_id,
        'state': state,
        }
    printAndLog('[%s] Create Wkf Workitem with values %s' % (obj_id, infoValue))
    if COMMIT:
        if PSYCOPG:
            keys = ['act_id', 'inst_id', 'state']
            vals = [act_id, inst_id, state]
            cur.execute("""INSERT INTO wkf_workitem (%s) values (%s);""" % (keys, vals))
            rows = cur.fetchall()
            return rows[0]
        else:
            res = BaseDbIntegration.Create('workflow.workitem', infoValue)
        return res
    return -1


def getWkfWorkitem(inst_id):
    if not inst_id:
        return {}
    cur.execute("""SELECT id, act_id, inst_id, state, subflow_id from wkf_workitem where inst_id = %s;""" % (inst_id))
    rows = cur.fetchall()
    wkf_list = dictify(('id', 'act_id', 'inst_id', 'state', 'subflow_id'), rows)
#     if PSYCOPG:
#         cur.execute("""SELECT id, act_id, inst_id, state, subflow_id from wkf_workitem where inst_id = %s;""" % (inst_id))
#         rows = cur.fetchall()
#         wkf_list = dictify(('id', 'act_id', 'inst_id', 'state', 'subflow_id'), rows)
#     else:
#         wkf_list = BaseDbIntegration.GetDetailsSearch('workflow.workitem', [('inst_id', '=', inst_id)], 
#                                                   ['id', 'act_id', 'inst_id', 'state', 'subflow_id'])
    for wkf_dict in wkf_list:
        return wkf_dict
    return {}


def updateWorkitem(wkf_id, act_id):
    printAndLog('Update Workitem %s with res_id %s' % (wkf_id, act_id))
    if COMMIT:
        if PSYCOPG:
            cur.execute("""UPDATE wkf_workitem act_id = %s where id = %s;""" % (act_id, wkf_id))
            rows = cur.fetchall()
        else:
            BaseDbIntegration.UpdateValue('workflow.workitem', [wkf_id], {'act_id': act_id})
        

def checkFixSingleObj(model, objDict, wkf_id, activity_dict):
    obj_id = objDict.get('id')
    obj_state = objDict.get('state')
    if obj_state == 'undermodify':
        obj_state = 'released'
    expected_act_id = activity_dict.get(obj_state)
    if not expected_act_id:
        printAndLog('[ERROR] Wrong Mapping between state %s and wkf_inst_dict %s, objDict %s' % (obj_state, activity_dict, objDict))
        return
    wkf_inst_dict = getWkfInstance(model, obj_id, wkf_id)
    if not wkf_inst_dict:
        inst_id = createWkfInstance(model, wkf_id, obj_id)
    else:
        inst_id = wkf_inst_dict.get('id')
    workitem_dict = getWkfWorkitem(inst_id)
    if not workitem_dict:
        createWkfWorkitem(expected_act_id, inst_id, obj_id)
        return 
    workitem_id = workitem_dict.get('id')
    real_act_id = workitem_dict.get('act_id')
    if expected_act_id != real_act_id:
        updateWorkitem(workitem_id, expected_act_id)

printAndLog('COMMIT %s, PSYCOPG %s' % (COMMIT, PSYCOPG))
res, cur = login()
if res:
    wkf_dict = getCorrectWorkflow()
    wkf_id = wkf_dict.get('id')
    wkf_obj = wkf_dict.get('object')
    if wkf_id:
        activity_dict = getWorkflowActivity(wkf_id)
        objList = getObjectList(wkf_obj)
        counter = len(objList)
        for index, objDict in enumerate(objList):
            checkFixSingleObj(wkf_obj, objDict, wkf_id, activity_dict)
            printAndLog('[%s / %s]' % (index, counter))
        
printAndLog('Done')

outFileLog.close()