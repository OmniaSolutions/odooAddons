# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-2013 Serpent Consulting Services (<http://www.serpentcs.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
############################################################################
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time

from openerp import pooler, tools
from openerp.report import report_sxw
from openerp.tools.translate import _

one_week = relativedelta(days=7)
num2day = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

def to_hour(h):
    return int(h), int(round((h - int(h)) * 60, 0))

class attendance_by_week(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(attendance_by_week, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_emp_ids': self.get_emp_ids,
            'hour2str':self.hour2str,
            'get_week':self.get_week,
            'get_attandance':self.get_attandance,
            'get_emp_name':self.get_emp_name,
        })

    def hour2str(self, h):
        hours = int(h)
        minutes = int(round((h - hours) * 60, 0))
        return '%02dh%02d' % (hours, minutes)

    def get_emp_ids(self,datas,context=None):
        emp_ids = datas['active_ids']
        return emp_ids
    
    def get_emp_name(self, ids):
        obj_emp = pooler.get_pool(self.cr.dbname).get('hr.employee')
        emp_ids =ids 
        if emp_ids:
            emp_name = obj_emp.read(self.cr, self.uid, emp_ids,['name'])
        return emp_name['name']

    def get_week(self,datas,context=None):
        start_date = datetime.strptime(datas['form']['init_date'], '%Y-%m-%d')
        end_date = datetime.strptime(datas['form']['end_date'], '%Y-%m-%d')
        first_monday = start_date - relativedelta(days=start_date.date().weekday())
        last_monday = end_date + relativedelta(days=7 - end_date.date().weekday())
        monday, n_monday = first_monday, first_monday + one_week
        
        week_first=[]
        week_last =[]
        week_end = []
        while monday != last_monday:
            if last_monday < first_monday:
                first_monday, last_monday = last_monday, first_monday 
            week_end.append(monday + relativedelta(days=7 - monday.date().weekday()))
            week_first.append(monday)
            week_last.append(last_monday)
            monday, n_monday = n_monday, n_monday + one_week
        return week_first, week_last, week_end
                
    def get_attandance(self, ids, week_first,week_last):
        start = week_first 
        end = week_first + relativedelta(days=7 - week_first.date().weekday())
         
        obj_emp = pooler.get_pool(self.cr.dbname).get('hr.employee')
        emp_ids = ids
        if emp_ids:
            emp = obj_emp.read(self.cr, self.uid, [emp_ids], ['id', 'name'])
            sql = '''
                select action, att.name
                from hr_employee as emp inner join hr_attendance as att
                     on emp.id = att.employee_id
                where att.name between %s and %s and emp.id = %s
                order by att.name
                '''
            for idx in range(7):
                self.cr.execute(sql, (start.strftime('%Y-%m-%d %H:%M:%S'), (start + relativedelta(days=idx+1)).strftime('%Y-%m-%d %H:%M:%S'), emp_ids))
                attendances = self.cr.dictfetchall()
                week_wh = {}
                # Fake sign ins/outs at week ends, to take attendances across week ends into account
                # XXX this is wrong for the first sign-in ever and the last sign out to this date
                if attendances and attendances[0]['action'] == 'sign_out':
                    attendances.insert(0, {'name': start.strftime('%Y-%m-%d %H:%M:%S'), 'action': 'sign_in'})
                if attendances and attendances[-1]['action'] == 'sign_in':
                    attendances.append({'name': end.strftime('%Y-%m-%d %H:%M:%S'), 'action': 'sign_out'})
                # sum up the attendances' durations
                ldt = None
                for att in attendances:
                    dt = datetime.strptime(att['name'], '%Y-%m-%d %H:%M:%S')
                    if ldt and att['action'] == 'sign_out':
                        week_wh[ldt.date().weekday()] = week_wh.get(ldt.date().weekday(), 0) + (float((dt - ldt).seconds)/3600)
                    else:
                        ldt = dt
        return week_wh 
            
report_sxw.report_sxw('report.hr.attendance.allweeks.webkit', 'hr.employee', 'addons/hr_attendance_webkit/report/timesheet.mako', parser=attendance_by_week, header='internal')
# vim:noexpandtab:tw=0
