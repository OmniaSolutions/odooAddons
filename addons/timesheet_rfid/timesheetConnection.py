'''
Created on Feb 13, 2015

@author: openerp
'''
from osv import osv, fields
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
import pytz
from datetime import datetime,timedelta, date
import time
import logging
_logger = logging.getLogger(__name__)
from dateutil import parser
import calendar
from mako.template import Template
import sys

#CURRENT_DATETIME = datetime.utcnow()#.replace(tzinfo=None, minute=0, second=0, hour=8, microsecond=0) #UNCOMMENT FOR DATETIME TEST
AFTERNOON_AUTOCOMPLETE_HOUR_UTC = 16
MORNING_HOUR = 6
EVENING_HOUR = 15
MIDNIGHT_HOUR = 22

def correctDate(fromTimeStr, context):
    serverUtcTime=parser.parse(fromTimeStr)
    hoursToCorrectTimedelta = serverUtcTime.replace(tzinfo=pytz.utc).astimezone(pytz.timezone(context.get('tz','Europe/Rome'))).utcoffset()
    return serverUtcTime - hoursToCorrectTimedelta

def correctDateForComputation(fromTimeStr, context):
    serverUtcTime=parser.parse(fromTimeStr)
    return serverUtcTime.replace(tzinfo=pytz.utc).astimezone(pytz.timezone(context.get('tz','Europe/Rome'))).replace(tzinfo=None)

class TimesheetConnection(osv.osv):
    _inherit='hr.employee'
    
    def getUidAndName(self, cr, uid, vals, context={}):
        employee_name = ''
        employee_id = self.search(cr, uid, [('otherid','=',vals)])
        if employee_id:
            employee_name = self.browse(cr, uid, employee_id[0]).name
        return {'employee_id':employee_id, 'employee_name': employee_name}
    
    def getEmployeeIdAndUserId(self, cr, uid, tagId, context={}):
        """
            get the employee id and the user id
        """
        employee_ids = self.search(cr, uid, [('otherid','=',tagId)])
        for brwE in self.browse(cr, uid, employee_ids):
            return brwE.id,brwE.user_id.id,brwE.name
        return False,False,False
        
    def getTimesheetInfos(self, cr, uid, vals, context = {}):
        '''
            *
            collect and send timesheet infos
            *
            vals: [employee_id,user_id, targetDate]
        '''
        employee_id     = vals[0]
        user_id         = vals[1]
        targetDate      = vals[2]
        rootContr       = vals[3]
        daysList, sheet_id, sheetState  = self.getDaysAndSheet(cr, uid, employee_id, targetDate, context = {})
        attendances                     = self.getAttendancesBySheetAndDays(cr, uid, user_id, sheet_id, daysList, context)
        timesheetDict                   = self.getTimesheetActivities(cr, uid, sheet_id, context)
        accountList, parentsForCombo    = self.computeAccountList(cr, uid, user_id, rootContr, context={})
        outDict = { 
                    'accountList'       : accountList,
                    'daysList'          : daysList,
                    'timesheetDict'     : timesheetDict,
                    'sheet_id'          : sheet_id,
                    'sheetReadonly'     : self.computeSheetState(sheetState),
                    'timeAttDiff'       : attendances,
                    'parentsForCombo'   : parentsForCombo,
                    }
        return outDict
        
    def computeSheetState(self, sheetState):
        sheetReadonly = False
        if sheetState == 'confirm':
            sheetReadonly = True
        return sheetReadonly
        
    def computeAccountList(self, cr, uid, user_id, rootContr, context={}):
        def parentRecursion(oggBrse):
            if oggBrse.parent_id:
                grandParentName = oggBrse.parent_id.name
                if rootContr == grandParentName:
                    return True
                return parentRecursion(oggBrse.parent_id)
            return False
        accAccObj = self.pool.get('account.analytic.account')
        projProjObj = self.pool.get('project.project')
        accIdsPre = accAccObj.search(cr, uid, [('type','in',['normal', 'contract']), ('state', '<>', 'close'),('use_timesheets','=',1)], order='name')
        accIds = []
        for accId in accIdsPre:
            relatedProjects = projProjObj.search(cr, uid, [('analytic_account_id','=',accId)])
            for proj in relatedProjects:
                usersAllowed = projProjObj.browse(cr, uid, proj).members
                for member in usersAllowed:
                    if user_id == member.id:
                        accIds.append(accId)
                        break
                break
        accountList = []
        parents = ['']
        for oggBrse in accAccObj.browse(cr, uid, accIds, context):
            if oggBrse.parent_id:
                if parentRecursion(oggBrse.parent_id):
                    parentName = oggBrse.parent_id.name
                    if oggBrse.state not in ['close','cancelled'] and self.verifyRelatedProjectState(cr, uid, oggBrse, context):#oggBrse.project_id
                        if parentName not in parents:
                            parents.append(parentName)
                        accountList.append({
                                        'complete_name' : '%s / %s'%(parentName, oggBrse.name),
                                        'acc_id'        : oggBrse.id,
                                        'parent'        : oggBrse.parent_id.complete_name,
                                        'grandparent'   : oggBrse.parent_id.parent_id.complete_name,
                                        })
        return (accountList, parents)
        
    def verifyRelatedProjectState(self, cr, uid, acc_an_acc_brws, context={}):
        proj_proj_obj = self.pool.get('project.project')
        relatedProjIds = proj_proj_obj.search(cr,uid,[('analytic_account_id','=',acc_an_acc_brws.id)])
        for proj_id in relatedProjIds:
            projBrws = proj_proj_obj.browse(cr, uid,proj_id )
            if projBrws.state in ['close','cancelled']:
                return False
            break
        return True
        
    def getAttendancesBySheetAndDays(self, cr, uid, user_id, sheet_id, daysList, context={}):
        outdict = {}
        sheetDaysObj = self.pool.get('hr_timesheet_sheet.sheet.day')
        for elem in daysList:
            stringDate = elem.get('date')
            compDatetime = datetime.strptime(stringDate+' 1:1:1', DEFAULT_SERVER_DATETIME_FORMAT)
            if compDatetime:
                compDate = compDatetime.date()
                sheetdaysIds = sheetDaysObj.search(cr, uid, [('sheet_id.user_id','=',user_id),('name','=',compDate)])
                for idd in sheetdaysIds:
                    objBrwse = sheetDaysObj.browse(cr, uid, idd)
                    if objBrwse:
                        total_difference = objBrwse.total_difference
                        total_attendance = objBrwse.total_attendance
                        total_timesheet  = objBrwse.total_timesheet
                        outdict[str(compDatetime.day)] = [total_difference, total_attendance, total_timesheet]
        return outdict

    def getTimesheetActivities(self, cr, uid, sheet_id, context):
        '''
            return timesheet activities by sheet
        '''
        outDict = {}
        if sheet_id:
            hrsheet_obj = self.pool.get('hr.analytic.timesheet')
            timesheetIds = hrsheet_obj.search(cr, uid, [('sheet_id','=', sheet_id)], context)
            for timeBrws in hrsheet_obj.browse(cr, uid, timesheetIds, context):
                accBrwse = timeBrws.line_id
                if accBrwse.date in outDict.keys():
                    found = 0
                    for elem in outDict[accBrwse.date]:
                        if accBrwse.account_id.complete_name == elem.get('account_name'):
                            elem['unit_amount'] = float(elem.get('unit_amount'))+float(accBrwse.unit_amount)
                            found = 1
                            break
                    if found ==0:
                        outDict[accBrwse.date].append({'unit_amount':accBrwse.unit_amount,
                                                       'account_name':accBrwse.account_id.complete_name,
                                                       'account_id':accBrwse.account_id.id,
                                                       'description':accBrwse.name,
                                                       })
                else:
                    outDict[accBrwse.date] = [{'unit_amount':accBrwse.unit_amount,
                                               'account_name':accBrwse.account_id.complete_name,
                                               'account_id':accBrwse.account_id.id,
                                               'description':accBrwse.name, 
                                               }]
        return outDict
    
    def getDaysAndSheet(self, cr, uid, employeeId, targetDate=False, context={}):
        '''
            return days and sheet id
        '''
        if not targetDate:
            targetDate = datetime.utcnow().date()
        else:
            targetDate = datetime.strptime(targetDate+' 1:1:1', DEFAULT_SERVER_DATETIME_FORMAT).date()
        sheetSheetObj = self.pool.get('hr_timesheet_sheet.sheet')
        sheetIds = sheetSheetObj.search(cr, uid, [('date_from','<=',targetDate),('date_to','>=',targetDate),('employee_id','=',employeeId)])
        if not sheetIds:
            sheetIds.append(self.createSheet(cr, uid, sheetSheetObj, employeeId, targetDate, context))
        if len(sheetIds)==1:
            sheetId = sheetIds[0]
            sheetBrwse = sheetSheetObj.browse(cr, uid, sheetId)
            date_from = sheetBrwse.date_from
            date_to = sheetBrwse.date_to
            sheetState = sheetBrwse.state
            computed_date_from = datetime.strptime(date_from+' 1:1:1', DEFAULT_SERVER_DATETIME_FORMAT)
            computed_date_to = datetime.strptime(date_to+' 1:1:1', DEFAULT_SERVER_DATETIME_FORMAT)
            delta = computed_date_to - computed_date_from
            daysList = []
            for i in range(delta.days + 1):
                date = computed_date_from + timedelta(days=i)
                monthName = calendar.month_name[date.month]
                dayNumber = date.day
                today = False
                if date.date() == targetDate:
                    today = True
                dayDict ={
                          'dayNumber'  : dayNumber,
                          'monthName'  : monthName,
                          'date'       : str(date.date()),
                          'today'      : today,
                          }
                daysList.append(dayDict)
            return daysList, sheetId, sheetState
        return [],False, False
    
    def getUserIdFromEmployeeId(self, cr, uid, employee_id):
        '''
            Return user ID form employee_id
        '''
        brws = self.browse(cr, uid, employee_id)
        if brws:
            if brws.user_id:
                return brws.user_id.id
        raise osv.orm.except_orm('getUserIdFromEmployeeId', 'Unable to get user ID from employee ID.')
        
    def attendance_action_change_custom(self, cr, uid, employee_id, context = {}):
        '''
            set sign in
        '''
        return self.singInOut(cr, uid, employee_id, datetime.utcnow().replace(microsecond=0), context)
        
    def makeTests(self, cr, uid, context={}):
        '''
            Called from "Test Feed" menu
        '''
        for empId, dateTime in self.getTestList():
            self.singInOut(cr, uid, empId, correctDate(str(dateTime),context), context)
            
    def getTestList(self):
        """
            Import a generic module from solverDir 
        """
        import test
        filePath='openerp.addons.timesheet_rfid.test.test'
        if filePath in sys.modules:
            mod=sys.modules[filePath]
            mod=reload(mod)
            return mod.HOURS_LIST
        
    def singInOut(self, cr, uid, employee_id, currentDateTime, context):
        '''
            Set sign_in or sign_out
        ''' 
        _logger.info("Call from consuntivator singInOut employee_id %s"%(str(employee_id)))
        outString = 'Action not computed'
        uid = self.getUserIdFromEmployeeId(cr, uid, employee_id)
        hrAttendanceObj = self.pool.get('hr.attendance')
        sheetObj = self.pool.get('hr_timesheet_sheet.sheet')
        date = currentDateTime.date()
        sheet_ids = sheetObj.search(cr, uid, [('date_from','<=',date),('date_to','>=',date),('employee_id','=',employee_id)])
        if not sheet_ids:
            sheet_ids = [self.createSheet(cr, uid, sheetObj, employee_id, date, context)]
            context['sheet_id'] = sheet_ids[0]
        else:
            context['sheet_id'] = sheet_ids[0]
        attendanceIds = hrAttendanceObj.search(cr, uid, [('employee_id','=',employee_id)], limit=1, order='name DESC')
        if not attendanceIds:
            outString = self.computeAndWrite(cr, uid, currentDateTime, employee_id, hrAttendanceObj, 'sign_in', context)
        else:
            lastAction = hrAttendanceObj.browse(cr, uid, attendanceIds[-1], context).action
            if lastAction == 'sign_in':
                outString = self.computeAndWrite(cr, uid, currentDateTime, employee_id, hrAttendanceObj, 'sign_out', context)
            elif lastAction == 'sign_out':
                outString = self.computeAndWrite(cr, uid, currentDateTime, employee_id, hrAttendanceObj, 'sign_in', context)
            else:
                raise Exception("No Action Defined")
        return outString
    
    def computeAndWrite(self, cr, uid, date, employee_id, hrAttendanceObj, action, context):
        '''
            Compute and write vals for attendances creation
        '''
        vals = self.computeVals(date, employee_id, action, context)
        if self.writeAction(cr, uid, employee_id, hrAttendanceObj, vals, context):
            return self.returnOutStringFromAction(action, employee_id)

    def returnOutStringFromAction(self, action, employee_id):
        '''
            Return successful string for sign in/out
        '''
        outString = 'Action not computed'
        if action == 'sign_in':
            outString = 'Entrata segnata'
            _logger.info("Signed in for employee_id = %s"%str(employee_id))
        elif action == 'sign_out':
            outString = 'Uscita segnata'
            _logger.info("Signed out for employee_id = %s"%str(employee_id))
        else:
            _logger.error("Signed action not valid: %s"%str(action))
        return outString
        
    def getNextUserAction(self, cr, uid, tagId, context):
        '''
            Return next action for consuntivator
        '''
        outAction = 'Not computed by server'
        currentDateTime = datetime.utcnow()
        date = currentDateTime.date()
        midnightTarget = datetime(year=date.year,month=date.month,day=date.day,hour=0,minute=0,second=0)
        morningTarget = datetime(year=date.year,month=date.month,day=date.day,hour=MORNING_HOUR,minute=0,second=0)
        eveningTarget = datetime(year=date.year,month=date.month,day=date.day,hour=EVENING_HOUR,minute=0,second=0)
        midnightOldTarget = datetime(year=date.year,month=date.month,day=date.day,hour=MIDNIGHT_HOUR,minute=59,second=59)
        hrAttendanceObj = self.pool.get('hr.attendance')
        employee_ids = self.search(cr, uid, [('otherid','=',tagId)])
        for employee_id in employee_ids:
            attendance = hrAttendanceObj.search(cr, uid, [('employee_id','=',employee_id)], limit=1, order='name DESC')
            if attendance:
                attendanceBrws = hrAttendanceObj.browse(cr, uid, attendance[-1], context)
                lastAction = attendanceBrws.action
                datetimeActStr = attendanceBrws.name
                datetimeAct = datetime.strptime(datetimeActStr, DEFAULT_SERVER_DATETIME_FORMAT)
                if currentDateTime>=midnightTarget and currentDateTime<=morningTarget:            #00:00 --> 8:00
                    if datetimeAct.date() == date and lastAction == 'sign_in':
                        outAction = 'Uscita'
                    else:
                        outAction = 'Entrata'
                elif currentDateTime>=morningTarget and currentDateTime<=eveningTarget:           #08:00 --> 19:00
                    if lastAction == 'sign_in':    
                        outAction = 'Uscita'
                    else:
                        outAction = 'Entrata'
                elif currentDateTime>=eveningTarget and currentDateTime<=midnightOldTarget:       #19:00 --> 23:59:59
                    outAction = 'Uscita'
                return outAction
            else:
                outAction = 'Entrata'
        return outAction


    def getLastAttendenceAction(self, cr, uid, vals, context):
        """
            return the next user action the the user will do if press the button
        """
        employee_id, timeOutSign = vals
        seconds = '0'
        hrAttendanceObj = self.pool.get('hr.attendance')
        attendance = hrAttendanceObj.search(cr, uid, [('employee_id','=',employee_id)], limit=1, order='name DESC')
        if attendance:
            attendanceBrws = hrAttendanceObj.browse(cr, uid, attendance[-1], context)
            lastAttStrDT = attendanceBrws.trueDateTime
            if not lastAttStrDT:
                lastAttStrDT = attendanceBrws.name
            compDatetime = datetime.strptime(lastAttStrDT, DEFAULT_SERVER_DATETIME_FORMAT)
            datetimeNow = datetime.utcnow().replace(microsecond = 0)
            timediff = datetimeNow-compDatetime
            if timediff < timedelta(seconds=timeOutSign):
                return 'wait'
            return attendanceBrws.action
        return False

    def createSheet(self, cr, uid, sheetObj, employee_id, date, context):
        '''
            Create a sheet for timesheet_sheet.sheet object
        '''
        date_from, date_to = self._getWeekFromTo(date)
        vals = {
                'date_from'     : date_from,
                'date_to'       : date_to,
                'employee_id'   : employee_id,
                'user_id'       : uid,
                'company_id'    : self.pool.get('account.tax.code')._default_company(cr, uid),
                }
        return sheetObj.create(cr, uid, vals, context)
        
    def _getWeekFromTo(self, date = False):
        '''
            Get dates for create sheet
        '''
        if not date:
            date = datetime.utcnow().date()
        weekday = date.weekday()
        mondayDate = date+timedelta(-weekday)
        sundayDate = mondayDate+timedelta(6)
        return mondayDate,sundayDate
        
    def computeVals(self,tarDatetime, employee_id, action, context):
        '''
            Compute vals for write
        '''
        vals={}
        vals['action']      = action
        vals['name']        = str(tarDatetime)
        vals['day']         = str(tarDatetime.date())
        vals['employee_id'] = employee_id
        return vals

    def writeAction(self, cr, uid, employeeID, hrAttendanceObj, vals={}, context = {}):
        '''
            write sign-in and sign-out
        '''
        return hrAttendanceObj.create(cr, 1, vals, context)
    
TimesheetConnection()

class timesheetSheetConnection(osv.osv):
    _inherit='hr_timesheet_sheet.sheet'
    
    def _getEmployeeCost(self, cr, uid, emp_id, context=None):
        """
            Return cost of a human resource ( 0.0 if not managed )
        """
        emp_obj = self.pool.get('hr.employee')
        if emp_id:
            emp = emp_obj.browse(cr, uid, emp_id, context=context)
            if emp.product_id:
                return emp.product_id.standard_price            # Resource cost 
        return 0.0
    
    def action_compile_timesheet(self, cr, uid, vals, context={}):
        """
            create or modify attendances
        """
        hrsheet_obj = self.pool.get('hr.analytic.timesheet')
        actxcod_obj = self.pool.get('account.tax.code')
        hrEmployeeObj = self.pool.get('hr.employee')
        _logger.info("Action_compile_timesheet Start Looping on Vals - %s"%str(vals))
        for timesheet in vals:
            employeeBrwse = hrEmployeeObj.browse(cr, uid, timesheet.get('employee_id'))
            user_id = employeeBrwse.user_id.id
            hours = timesheet.get('hours')
            if not hours:
                hours = 0
            acc_id = timesheet.get('acc_id')
            computedDate = timesheet.get('date')
            timesheetDesc=timesheet.get('desc','/')
            if len(timesheetDesc)<=0:
                timesheetDesc='/'
            hrsheet_defaults = {
                                    'product_uom_id'        :hrsheet_obj._getEmployeeUnit(cr, uid),
                                    'product_id'            :hrsheet_obj._getEmployeeProduct(cr, uid),
                                    'general_account_id'    :hrsheet_obj._getGeneralAccount(cr, uid),
                                    'journal_id'            :hrsheet_obj._getAnalyticJournal(cr, uid),
                                    'date'                  :computedDate,
                                    'user_id'               :user_id,
                                    'to_invoice'            :0,# 1 = Yes(100%) int(toInvoice), imposato a invoicable 100%
                                    'account_id'            :acc_id,
                                    'unit_amount'           :hours,
                                    'company_id'            :actxcod_obj._default_company(cr, uid),
                                    'amount'                :self._getEmployeeCost(cr,uid, employeeBrwse.id)*float(hours)*(-1),      # Recorded negative because it's a cost
                                    'name'                  :timesheetDesc,
                                    'sheet_id'              :timesheet.get('sheet_id'),
                               }
            alreadyWritten = hrsheet_obj.search(cr, uid, [('account_id','=',acc_id),('date','=',computedDate),('user_id','=',user_id)])
            if len(alreadyWritten)==1:
                #nel caso in cui ci fossero piu' attendances collegate al medesimo sheet del medesimo giorno al momento non applico le modifiche
                #se ne trovo una faccio una modifica senno' la creo
                #non posso fare la scrittura per tutte le attendances perche' il totale di ognuna sara' diverso.
                res = hrsheet_obj.write(cr, uid, alreadyWritten[0],hrsheet_defaults)
                if not res:
                    raise Exception('Update timesheet failed')
                else:
                    _logger.info("Update data from consuntivator ID:[%s]->[%s]"%(str(alreadyWritten[0]),str(hrsheet_defaults)))
            elif len(alreadyWritten)==0:
                create_id=hrsheet_obj.create(cr, uid, hrsheet_defaults, context)
                if not create_id:
                    raise Exception('Create timesheet failed')
                else:
                    _logger.info("New data from consuntivator ID: [%s]->[%s]"%(str(create_id),str(hrsheet_defaults)))
        _logger.info("Action_compile_timesheet DONE !!")
        return True

timesheetSheetConnection()
