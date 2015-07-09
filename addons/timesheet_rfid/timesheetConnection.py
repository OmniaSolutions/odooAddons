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
        
    def getTimesheetInfos(self, cr, uid, vals, context = {}):
        '''
            collect and send timesheet infos
        '''
        uid = self.getUserIdFromEmployeeId(cr, uid, vals[0])
        daysList, sheet_id, sheetState = self.getDaysAndSheet(cr, uid, vals[0], vals[1], context = {})
        attendances = self.getAttendancesBySheetAndDays(cr, uid, sheet_id, daysList, context)
        sheetReadonly = False
        if sheetState == 'confirm':
            sheetReadonly = True
        timesheetDict = self.getTimesheetActivities(cr, uid, vals[0], sheet_id, context)
        accAccObj = self.pool.get('account.analytic.account')
        accIdsPre = accAccObj.search(cr, uid, [('type','in',['normal', 'contract']), ('state', '<>', 'close'),('use_timesheets','=',1)], order='name')
        projProjObj = self.pool.get('project.project')
        
        employee_id = vals[0]
        userId = self.pool.get('hr.employee').browse(cr, uid, employee_id).user_id.id
        accIds = []
        for accId in accIdsPre:
            relatedProjects = projProjObj.search(cr, uid, [('analytic_account_id','=',accId)])
            for proj in relatedProjects:
                usersAllowed = projProjObj.browse(cr, uid, proj).members
                for member in usersAllowed:
                    if userId == member.id:
                        accIds.append(accId)
                        break
        brwsList = accAccObj.browse(cr, uid, accIds, context)
        accountList = []
        for oggBrse in brwsList:
            grandparent = ''
            parent = ''
            if oggBrse.parent_id:
                parent=oggBrse.parent_id.complete_name
            if oggBrse.parent_id.parent_id:
                grandparent = oggBrse.parent_id.parent_id.complete_name
            accountList.append({
                            'complete_name' : unicode(oggBrse.complete_name),
                            'acc_id'        : oggBrse.id,
                            'parent'        : parent,
                            'grandparent'   : grandparent,
                            })
        outDict = { 
                    'accountList'   : accountList,
                    'daysList'      : daysList,
                    'timesheetDict' : timesheetDict,
                    'sheet_id'      : sheet_id,
                    'sheetReadonly' : sheetReadonly,
                    'timeAttDiff'   : attendances,
                    }
        return outDict
        
    def getAttendancesBySheetAndDays(self, cr, uid, sheet_id, daysList, context={}):
        outdict = {}
        sheetDaysObj = self.pool.get('hr_timesheet_sheet.sheet.day')
        for elem in daysList:
            stringDate = elem.get('date')
            compDatetime = datetime.strptime(stringDate+' 1:1:1', DEFAULT_SERVER_DATETIME_FORMAT)
            if compDatetime:
                compDate = compDatetime.date()
                sheetdaysIds = sheetDaysObj.search(cr, uid, [('sheet_id.user_id','=',uid),('name','=',compDate)])
                for idd in sheetdaysIds:
                    objBrwse = sheetDaysObj.browse(cr, uid, idd)
                    if objBrwse:
                        total_difference = objBrwse.total_difference
                        total_attendance = objBrwse.total_attendance
                        total_timesheet  = objBrwse.total_timesheet
                        outdict[str(compDatetime.day)] = [total_difference, total_attendance, total_timesheet]
        return outdict
        
    def getTimesheetActivities(self, cr, uid, userID, sheet_id, context):
        '''
            return timesheet activities by sheet
        '''
        outDict = {}
        if sheet_id:
            hrsheet_obj = self.pool.get('hr.analytic.timesheet')
            timesheetIds = hrsheet_obj.search(cr, uid, [('sheet_id','=', sheet_id)], context)
            for timeId in timesheetIds:
                accBrwse = hrsheet_obj.browse(cr, uid, timeId, context).line_id
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
                weekDayId = calendar.weekday(date.year, date.month, date.day)
                dayName   = calendar.day_name[weekDayId]
                today = False
                if date.date() == targetDate:
                    today = True
                dayDict ={
                          'dayName'    : dayName,
                          'dayNumber'  : dayNumber,
                          'monthName'  : monthName,
                          'date'       : str(date.date()),
                          'today'      : today,
                          }
                print date
                daysList.append(dayDict)
            return daysList, sheetId, sheetState
        return [],False, False
    
    def getUserIdFromEmployeeId(self, cr, uid, employee_id):
        brws = self.browse(cr, uid, employee_id)
        if brws:
            return brws.user_id.id
        
    def attendance_action_change_custom(self, cr, uid, employee_id, context = {}):
        '''
            set sign in
        '''
        return self.singInOut(cr, uid, employee_id, datetime.utcnow(), context)
        
    def makeTests(self, cr, uid, context={}):
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
        uid = self.getUserIdFromEmployeeId(cr, uid, employee_id)
        hrAttendanceObj = self.pool.get('hr.attendance')
        sheetObj = self.pool.get('hr_timesheet_sheet.sheet')
        date = currentDateTime.date()
        sheet_ids = sheetObj.search(cr, uid, [('date_from','<=',date),('date_to','>=',date),('employee_id','=',employee_id)])
        if not sheet_ids:
            sheet_ids = [self.createSheet(cr, uid, sheetObj, employee_id, date, context)]
            context['sheet_id'] = sheet_ids[0]
        attendanceIds = hrAttendanceObj.search(cr, uid, [('employee_id','=',employee_id)], limit=1, order='name DESC')
        if len(attendanceIds)>0:
            brws = hrAttendanceObj.browse(cr, uid, attendanceIds[-1], context)
            if brws:
                action = brws.action
                if action:
                    if not self.computeDateRange(cr, uid, employee_id, hrAttendanceObj, currentDateTime, context):
                        return False
                else:
                    logging.log('invalid action')
        else:

            for sheet_id in sheet_ids:
                vals = {
                        'action'        : 'sign_in',
                        'name'          : str(date)+' '+str(currentDateTime.time()).split('.')[0],
                        'day'           : str(date),
                        'employee_id'   : employee_id,
                }
                context['sheet_id']=sheet_id
                if not self.writeAction(cr, uid, employee_id, hrAttendanceObj, vals, context):
                    return False
                break
        attendance = hrAttendanceObj.search(cr, uid, [('employee_id','=',employee_id)], limit=1, order='name DESC')
        if attendance:
            lastAction = hrAttendanceObj.browse(cr, uid, attendance[-1], context).action
            if lastAction == 'sign_out':
                return 'Uscita segnata'
            elif lastAction == 'sign_in':
                return 'Entrata segnata'
        return False
        
    def getNextUserAction(self, cr, uid, vals, context):
        outAction = 'Not computed by server'
        currentDateTime = datetime.utcnow()
        date = currentDateTime.date()
        midnightTarget = datetime(year=date.year,month=date.month,day=date.day,hour=0,minute=0,second=0)
        morningTarget = datetime(year=date.year,month=date.month,day=date.day,hour=MORNING_HOUR,minute=0,second=0)
        eveningTarget = datetime(year=date.year,month=date.month,day=date.day,hour=EVENING_HOUR,minute=0,second=0)
        midnightOldTarget = datetime(year=date.year,month=date.month,day=date.day,hour=MIDNIGHT_HOUR,minute=59,second=59)
        employee_name = vals.get('employee_name',False)
        if employee_name:
            hrAttendanceObj = self.pool.get('hr.attendance')
            employee_ids = self.search(cr, uid, [('name','=',employee_name)])
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
            
    def createSheet(self, cr, uid, sheetObj, employee_id, date, context):
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
        if not date:
            date = datetime.utcnow().date()
        weekday = date.weekday()
        mondayDate = date+timedelta(-weekday)
        sundayDate = mondayDate+timedelta(6)
        return mondayDate,sundayDate
        
    def computeDateRange(self, cr, uid, employeeID, hrAttendanceObj, currentDatetime, context = {}):
        '''
            compute and set sign-in and sign-out
        '''
        def commonOperations(cr, uid, hrAttendanceObj, employeeID, currentDatetime, vals, context={}):
            action = self.setOldAttendances(cr, uid, hrAttendanceObj, employeeID, currentDatetime, context)
            if action == 'sign_in':
                vals['action']  ='sign_out'
            elif action == 'sign_out':
                vals['action']  ='sign_in'
            else:
                return False
            trueDateTime = currentDatetime.replace(microsecond=0)
            vals = self.computeVals(trueDateTime, employeeID, vals['action'], context)
            if not self.writeAction(cr, uid, employeeID, hrAttendanceObj, vals, context):
                return False
            
        def commonMorningOperation(cr, uid, hrAttendanceObj, employeeID, vals, morningTarget, currentDatetime, context):
            if not self.setOldAttendances(cr, uid, hrAttendanceObj, employeeID, currentDatetime, context):
                return False
            vals = self.computeVals(morningTarget, employeeID, 'sign_in', context)
            if not self.writeAction(cr, uid, employeeID, hrAttendanceObj, vals, context):
                return False
            trueDateTime = currentDatetime.replace(microsecond=0)
            vals = self.computeVals(trueDateTime, employeeID, 'sign_out', context)
            if not self.writeAction(cr, uid, employeeID, hrAttendanceObj, vals, context):
                return False
            
        def eveningOperations(cr, uid, employeeID, date, hrAttendanceObj, vals, morningTarget, currentDatetime, context):
            todaySignIn = hrAttendanceObj.search(cr, uid, [('employee_id','=',employeeID), ('day', '=', date)])
            if len(todaySignIn) == 0:
                return commonMorningOperation(cr, uid, hrAttendanceObj, employeeID, vals, morningTarget, currentDatetime, context)
            else: 
                return commonOperations(cr, uid, hrAttendanceObj, employeeID, currentDatetime, vals, context)
            
        def operations(cr, uid, employeeID, hrAttendanceObj, currentDateTime, context = {}):
            date = currentDatetime.date()
            midnightTarget = datetime(year=date.year,month=date.month,day=date.day,hour=0,minute=0,second=0)
            morningTarget = datetime(year=date.year,month=date.month,day=date.day,hour=MORNING_HOUR,minute=0,second=0)
            eveningTarget = datetime(year=date.year,month=date.month,day=date.day,hour=EVENING_HOUR,minute=0,second=0)
            midnightOldTarget = datetime(year=date.year,month=date.month,day=date.day,hour=MIDNIGHT_HOUR,minute=59,second=59)
            vals = {
                    'action'        : False,
                    'name'          : False,
                    'day'           : False,
                    'employee_id'   : employeeID,
            }
            if currentDateTime>=midnightTarget and currentDateTime<=morningTarget:            #00:00 --> 8:00
                return commonOperations(cr, uid, hrAttendanceObj, employeeID, currentDateTime, vals, context)
            elif currentDateTime>=morningTarget and currentDateTime<=eveningTarget:           #08:00 --> 17:00
                return commonOperations(cr, uid, hrAttendanceObj, employeeID, currentDateTime, vals, context)
            elif currentDateTime>=eveningTarget and currentDateTime<=midnightOldTarget:       #17:00 --> 23:59:59
                return eveningOperations(cr, uid, employeeID, date, hrAttendanceObj, vals, morningTarget, currentDateTime, context)

        operations(cr, uid, employeeID, hrAttendanceObj, currentDatetime, context)
        return True
        
    def computeVals(self,tarDatetime, employee_id, action, context):
        vals={}
        vals['action']      = action
        vals['name']        = str(tarDatetime)
        vals['day']         = str(tarDatetime.date())
        vals['employee_id'] = employee_id
        return vals
        
    def setOldAttendances(self, cr, uid, hrAttendanceObj, employee_id, currentDateTime, context):
        def verifySign(lastDateTime):
            middayTarget = brwsDatetime.replace(hour=10, minute=01)
            if lastDateTime<middayTarget:
                return 'morning'
            else:
                return 'afternoon'
            return False
        
        def computeAndWrite(cr, uid, brwsDatetime, employee_id, action, hrAttendanceObj, hour, context):
            localDatetime = brwsDatetime.replace(hour=hour, minute=0)
            vals = self.computeVals(localDatetime, employee_id, action, context)
            res = self.writeAction(cr, uid, employee_id, hrAttendanceObj, vals)
            if not res:
                return False
            return res
            
        def bodyAndSendEmail(cr, uid, attIds, employee_id, context):
            body_html = self.computeBodyForMail(cr, uid, employee_id, attIds,context)
            self.send_mail(cr, uid, body_html=body_html, context=context) 
            return True
        
        attendances = hrAttendanceObj.search(cr, uid, [('employee_id','=',employee_id)],limit=1, order='name DESC')
        brwse = hrAttendanceObj.browse(cr, uid, attendances)[0]
        action = brwse.action
        date = datetime.strptime(brwse.day+' 1:1:1', DEFAULT_SERVER_DATETIME_FORMAT)
        brwsDatetime = datetime.strptime(brwse.name, DEFAULT_SERVER_DATETIME_FORMAT)
        res = verifySign(brwsDatetime)
        if action == 'sign_in' and date.date() != currentDateTime.date():
            if res == 'afternoon':
                tarDatetime = brwsDatetime.replace(hour=AFTERNOON_AUTOCOMPLETE_HOUR_UTC, minute=0)
                if brwsDatetime > tarDatetime:
                    tarDatetime = brwsDatetime + timedelta(minutes=1)
                vals = self.computeVals(tarDatetime, employee_id, 'sign_out', context)
                attMidId = self.writeAction(cr, uid, employee_id, hrAttendanceObj, vals)
                if not attMidId:
                    return False
                bodyAndSendEmail(cr, uid, [attMidId], employee_id, context)
                return 'sign_out'
            elif res == 'morning':
                attMidId = computeAndWrite(cr, uid, brwsDatetime, employee_id, 'sign_out', hrAttendanceObj, 10, context)
                if not attMidId:
                    return False
                bodyAndSendEmail(cr, uid, [attMidId], employee_id, context)
                return 'sign_out'
        return action
        
    def computeBodyForMail(self, cr, uid, employeeId, attendanceList=[], context={}):
        outBody = 'Salve,<br>'
        attendanceObj = self.pool.get('hr.attendance')
        employeeBrws = self.pool.get('hr.employee').browse(cr, uid, employeeId, context)
        outBody = outBody + "L'utente %s non ha timbrato le seguenti ore relative alla pausa pranzo:<br>"%(employeeBrws.name)
        for attId in attendanceList:
            attBrws = attendanceObj.browse(cr, uid, attId, context)
            outBody = outBody + "Azione %s in data e ora %s <br>"%(attBrws.action,correctDateForComputation(attBrws.name,context))
        outBody = outBody + "Le ore qui descritte sono state salvate dalla procedura automatica.<br> Cordiali Saluti"
        return outBody
        
    def send_mail(self, cr, uid,subject='[Timesheet Info]', body_html='', email_to=[], context=None):
        if not email_to:
            groupsObj = self.pool.get('res.groups')
            groupsIds = groupsObj.search(cr, uid, [('name','=','Manager')])
            for groupId in groupsIds:
                groupBrws = groupsObj.browse(cr, uid, groupId, context)
                categBrows = groupBrws.category_id
                if categBrows and categBrows.name == 'Human Resources':
                    for userBrws in groupBrws.users:
                        userEmail = userBrws.email
                        if userEmail:
                            email_to.append(userEmail)
                    break
        values = {}
        values['subject'] = subject
        values['body_html'] = body_html
        values['body'] = Template('MAIL_WORKFLOW_TEMPLATE').render_unicode(schedaObj=self)
        values['res_id'] = False
        mail_mail_obj = self.pool.get('mail.mail')
        for mailAddress in email_to:
            values['email_to'] = mailAddress
            try:
                msg_id = mail_mail_obj.create(cr, uid, values, context=context)
                if msg_id:
                    mail_mail_obj.send(cr, uid, [msg_id], context=context) 
            except Exception,ex:
                print ex
                print 'Mail not delivered to %s'%mailAddress
        return True

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
        for timesheet in vals:
            employeeBrwse = hrEmployeeObj.browse(cr, uid, timesheet.get('employee_id'))
            hours = timesheet.get('hours')
            if not hours:
                hours = 0
            acc_id = timesheet.get('acc_id')
            computedDate = timesheet.get('date')
            #computedDate = correctDate(computedDate, context).replace(tzinfo=None)
            hrsheet_defaults = {
                                    'product_uom_id':       hrsheet_obj._getEmployeeUnit(cr, uid),
                                    'product_id':           hrsheet_obj._getEmployeeProduct(cr, uid),
                                    'general_account_id':   hrsheet_obj._getGeneralAccount(cr, uid),
                                    'journal_id':           hrsheet_obj._getAnalyticJournal(cr, uid),
                                    'date':                 computedDate,
                                    'user_id':              employeeBrwse.user_id.id,
                                    'to_invoice':   1,#FIXME: Yes(100%) int(toInvoice), imposato a invoicable 100%
                                    'account_id':   acc_id,
                                    'unit_amount':  hours,
                                    'company_id':   actxcod_obj._default_company(cr, uid),
                                    'amount':       self._getEmployeeCost(cr,uid, employeeBrwse.id)*float(hours)*(-1),      # Recorded negative because it's a cost
                                    'name' :        timesheet.get('desc'),
                                    'sheet_id' :    timesheet.get('sheet_id'),
                               }
            alreadyWritten = hrsheet_obj.search(cr, uid, [('account_id','=',acc_id),('date','=',computedDate)])
            if len(alreadyWritten)==1:
                #FIXME: nel caso in cui ci fossero piu' attendances collegate al medesimo sheet del medesimo giorno al momento non applico le modifiche
                #se ne trovo una faccio una modifica senno' la creo
                #non posso fare la scrittura per tutte le attendances perche' il totale di ognuna sara' diverso.
                res = hrsheet_obj.write(cr, uid, alreadyWritten[0],hrsheet_defaults)
                if not res:
                    raise Exception('Write timesheet failed')
            elif len(alreadyWritten)==0:
                if not hrsheet_obj.create(cr, uid, hrsheet_defaults, context):
                    raise Exception('Write timesheet failed')
        return True

timesheetSheetConnection()
