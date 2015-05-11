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

def correctDate(fromTimeStr, context):
    serverUtcTime=parser.parse(fromTimeStr)
    return serverUtcTime.replace(tzinfo=pytz.utc).astimezone(pytz.timezone(context.get('tz','Europe/Rome')))

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
                            'id'            : oggBrse.id,
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
                                                       'description':accBrwse.name,
                                                       })
                else:
                    outDict[accBrwse.date] = [{'unit_amount':accBrwse.unit_amount,
                                               'account_name':accBrwse.account_id.complete_name,
                                               'description':accBrwse.name, 
                                               }]
        return outDict
    
    def getDaysAndSheet(self, cr, uid, employeeId, targetDate=False, context={}):
        '''
            return days and sheet id
        '''
        if not targetDate:
            targetDate = datetime.now().date()
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
                dayName   = calendar.day_abbr[weekDayId]
                dayDict ={
                          'dayName'    : dayName,
                          'dayNumber'  : dayNumber,
                          'monthName'  : monthName,
                          'date'       : str(date.date()),
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
        uid = self.getUserIdFromEmployeeId(cr, uid, employee_id)
        hrAttendanceObj = self.pool.get('hr.attendance')
        attendanceIds = hrAttendanceObj.search(cr, uid, [('employee_id','=',employee_id)], limit=1, order='name DESC')
        if len(attendanceIds)>0:
            brws = hrAttendanceObj.browse(cr, uid, attendanceIds[-1], context)
            if brws:
                action = brws.action
                if action:
                    self.computeDateRange(cr, uid, employee_id, action, hrAttendanceObj, context)
                else:
                    logging.log('invalid action')
        else:
            sheetObj = self.pool.get('hr_timesheet_sheet.sheet')
            dateTime = datetime.now()
            date = dateTime.date()
            sheet_ids = sheetObj.search(cr, uid, [('date_from','<=',date),('date_to','>=',date),('employee_id','=',employee_id)])
            if not sheet_ids:
                sheet_ids = [self.createSheet(cr, uid, sheetObj, employee_id, date, context)]

            for sheet_id in sheet_ids:
                vals = {
                        'action'        : 'sign_in',
                        'name'          : str(date)+' '+str(dateTime.time()).split('.')[0],
                        'day'           : str(date),
                        'employee_id'   : employee_id,
                }
                context['sheet_id']=sheet_id
                self.writeAction(cr, uid, employee_id, hrAttendanceObj, vals, context)
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
        currentDatetime = datetime.now()
        date = currentDatetime.date()
        midnightTarget = datetime(year=date.year,month=date.month,day=date.day,hour=0,minute=0,second=0)
        morningTarget = datetime(year=date.year,month=date.month,day=date.day,hour=8,minute=0,second=0)
        eveningTarget = datetime(year=date.year,month=date.month,day=date.day,hour=19,minute=0,second=0)
        midnightOldTarget = datetime(year=date.year,month=date.month,day=date.day,hour=23,minute=59,second=59)
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
                    if currentDatetime>=midnightTarget and currentDatetime<=morningTarget:            #00:00 --> 8:00
                        if datetimeAct.date() == date and lastAction == 'sign_in':
                            outAction = 'Uscita'
                        else:
                            outAction = 'Entrata'
                    elif currentDatetime>=morningTarget and currentDatetime<=eveningTarget:           #08:00 --> 19:00
                        if lastAction == 'sign_in':    
                            outAction = 'Uscita'
                        else:
                            outAction = 'Entrata'
                    elif currentDatetime>=eveningTarget and currentDatetime<=midnightOldTarget:       #19:00 --> 23:59:59
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
            date = datetime.now().date()
        weekday = date.weekday()
        mondayDate = date+timedelta(-weekday)
        sundayDate = mondayDate+timedelta(6)
        return mondayDate,sundayDate

    def computeDateRange(self, cr, uid, employeeID, action, hrAttendanceObj, context = {}):
        '''
            compute and set sign-in and sign-out
        '''
        currentDatetime = datetime.now()     
        date = currentDatetime.date()
        midnightTarget = datetime(year=date.year,month=date.month,day=date.day,hour=0,minute=0,second=0)
        morningTarget = datetime(year=date.year,month=date.month,day=date.day,hour=8,minute=0,second=0)
        eveningTarget = datetime(year=date.year,month=date.month,day=date.day,hour=19,minute=0,second=0)
        midnightOldTarget = datetime(year=date.year,month=date.month,day=date.day,hour=23,minute=59,second=59)
        vals = {
                'action'        : False,
                'name'          : False,
                'day'           : False,
                'employee_id'   : employeeID,
        }
        if currentDatetime>=midnightTarget and currentDatetime<=morningTarget:            #00:00 --> 8:00
            self.setOldAttendances(cr, uid, hrAttendanceObj, employeeID, context)
            self.writeAction(cr, uid, employeeID, hrAttendanceObj, context)
        elif currentDatetime>=morningTarget and currentDatetime<=eveningTarget:           #08:00 --> 19:00
            self.setOldAttendances(cr, uid, hrAttendanceObj, employeeID, context)
            self.writeAction(cr, uid, employeeID, hrAttendanceObj, context)
        elif currentDatetime>=eveningTarget and currentDatetime<=midnightOldTarget:       #19:00 --> 23:59:59
            if action == 'sign_out':
                self.setOldAttendances(cr, uid, hrAttendanceObj, employeeID, context)
                morningTarget = correctDate(str(morningTarget), context).replace(tzinfo=None)
                vals['action']  ='sign_in'
                vals['name']    = str(morningTarget)
                vals['day']     = str(morningTarget.date())
                self.writeAction(cr, uid, employeeID, hrAttendanceObj, vals, context)
                self.writeAction(cr, uid, employeeID, hrAttendanceObj, context)
            elif action == 'sign_in':
                todaySignIn = hrAttendanceObj.search(cr, uid, [('employee_id','=',employeeID), ('day', '=', date)])
                if len(todaySignIn) == 1:
                    self.writeAction(cr, uid, employeeID, hrAttendanceObj, context)
                elif len(todaySignIn) == 0:
                    self.setOldAttendances(cr, uid, hrAttendanceObj, employeeID, context)
                    morningTarget = correctDate(str(morningTarget), context).replace(tzinfo=None)
                    vals['action']  ='sign_in'
                    vals['name']    = str(morningTarget)
                    vals['day']     = str(morningTarget.date())
                    self.writeAction(cr, uid, employeeID, hrAttendanceObj, vals, context)
                    
                    self.writeAction(cr, uid, employeeID, hrAttendanceObj, context)
        
    def setOldAttendances(self, cr, uid, hrAttendanceObj, employee_id, context):
        attendances = hrAttendanceObj.search(cr, uid, [('employee_id','=',employee_id)],limit=1, order='name DESC')
        brwse = hrAttendanceObj.browse(cr, uid, attendances)[0]
        action = brwse.action
        date = datetime.strptime(brwse.day+' 1:1:1', DEFAULT_SERVER_DATETIME_FORMAT)
        if action == 'sign_in' and date.date()!=datetime.now().date():
            tar = datetime(year=date.year,month=date.month,day=date.day,hour=19,minute=0,second=0)
            vals={}
            vals['action']      = 'sign_out'
            vals['name']        = str(tar)
            vals['day']         = str(tar.date())
            vals['employee_id'] = employee_id
            self.writeAction(cr, uid, employee_id, hrAttendanceObj, vals)
        return True
        
    def writeAction(self, cr, uid, employeeID, hrAttendanceObj, vals=False, context = {}):
        '''
            write sign-in and sign-out
        '''
        timeZone = self.pool.get('res.users').browse(cr, uid, uid).tz
        if timeZone == False:
            context['tz']='Europe/Rome'
        else:
            context['tz']=timeZone
        date = correctDate(vals.get('name',''), context)
        if not vals:
            return super(TimesheetConnection,self).attendance_action_change(cr, uid, [employeeID], context)
        return hrAttendanceObj.create(cr, uid, vals, context)
    
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
            name = timesheet.get('account_name').split('/')[-1]
            acc_id = self.pool.get('account.analytic.account').search(cr, uid, [('type','in',['normal', 'contract']), ('state', '<>', 'close'),('use_timesheets','=',1),('name','=',name.strip())])
            computedDate = timesheet.get('date')
            computedDate = correctDate(computedDate, context).replace(tzinfo=None)
            hrsheet_defaults = {
                                    'product_uom_id':       hrsheet_obj._getEmployeeUnit(cr, uid),
                                    'product_id':           hrsheet_obj._getEmployeeProduct(cr, uid),
                                    'general_account_id':   hrsheet_obj._getGeneralAccount(cr, uid),
                                    'journal_id':           hrsheet_obj._getAnalyticJournal(cr, uid),
                                    'date':                 computedDate,
                                    'user_id':              employeeBrwse.user_id.id,
                                    'to_invoice':   1,#FIXME: Yes(100%) int(toInvoice), imposato a invoicable 100%
                                    'account_id':   acc_id[0],
                                    'unit_amount':  hours,
                                    'company_id':   actxcod_obj._default_company(cr, uid),
                                    'amount':       self._getEmployeeCost(cr,uid, employeeBrwse.id)*float(hours)*(-1),      # Recorded negative because it's a cost
                                    'name' :        timesheet.get('desc'),
                                    'sheet_id' :    timesheet.get('sheet_id'),
                               }
            alreadyWritten = hrsheet_obj.search(cr, uid, [('account_id','=',acc_id[0]),('date','=',computedDate)])
            if len(alreadyWritten)==1:
                #FIXME: nel caso in cui ci fossero piu' attendances collegate al medesimo sheet del medesimo giorno al momento non applico le modifiche
                #se ne trovo una faccio una modifica senno' la creo
                #non posso fare la scrittura per tutte le attendances perche' il totale di ognuna sara' diverso.
                hrsheet_obj.write(cr, uid, alreadyWritten[0],hrsheet_defaults)
            elif len(alreadyWritten)==0:
                hrsheet_obj.create(cr, uid, hrsheet_defaults, context)
        return True

timesheetSheetConnection()
