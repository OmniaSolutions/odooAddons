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

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time

from openerp import pooler
from openerp.report import report_sxw

one_day = relativedelta(days=1)
month2name = [0, 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

def hour2str(h):
    hours = int(h)
    minutes = int(round((h - hours) * 60, 0))
    return '%02dh%02d' % (hours, minutes)

class attendance_by_month(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(attendance_by_month, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'lengthmonth':self.lengthmonth,
            'get_month_year':self.get_month_year,
            'get_day_name':self.get_day_name,
            'get_emp_data':self.get_emp_data,
            'get_emp_ids':self.get_emp_ids,
        })

    def get_month_year(self, year, month):
        month = datetime(year, month, 1)
        print (month) 
        return  month2name[month.month]

    def lengthmonth(self, year,month):
        
        if month == 2 and ((year % 4 == 0) and ((year % 100 != 0) or (year % 400 == 0))):
            return 29
        return [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month]

    def get_day_name(self, year, month, day):
        days =[]
        name_of_day = datetime.weekday(datetime(year,month,day))
        if name_of_day == 0:
            return "Mon"
        elif name_of_day == 1:
            return "Tue"
        elif name_of_day == 2:
            return "Wed"
        elif name_of_day == 3:
            return "Thus"
        elif name_of_day == 4:
            return "Fri"
        elif name_of_day == 5:
            return "Sat"
        elif name_of_day == 6:
            return "Sun"
        
    def get_emp_ids(self,datas,context=None):
        emp_ids = datas['active_ids']
        return emp_ids

    def get_emp_data(self, ids, datas,context=None):
        obj_emp = pooler.get_pool(self.cr.dbname).get('hr.employee')
        emp_ids = ids
        month = datetime(datas['form']['year'], datas['form']['month'], 1)
        if emp_ids:
            for emp in obj_emp.read(self.cr, self.uid, [emp_ids], ['name']):
                wh_list=[]
                wh_name=[]
                total_wh = 0.0
                wh_name.append(emp['name'])
                today, tomor = month, month + one_day
                while today.month == month.month:
                    sql = '''
                    select action, att.name
                    from hr_employee as emp inner join hr_attendance as att
                         on emp.id = att.employee_id
                    where att.name between %s and %s and emp.id = %s
                    order by att.name
                    '''
                    self.cr.execute(sql, (today.strftime('%Y-%m-%d %H:%M:%S'), tomor.strftime('%Y-%m-%d %H:%M:%S'), emp['id']))
                    attendences = self.cr.dictfetchall()
                    wh = 0.0
                    # Fake sign ins/outs at week ends, to take attendances across week ends into account
                    if attendences and attendences[0]['action'] == 'sign_out':
                        attendences.insert(0, {'name': today.strftime('%Y-%m-%d %H:%M:%S'), 'action':'sign_in'})
                    if attendences and attendences[-1]['action'] == 'sign_in':
                        attendences.append({'name': tomor.strftime('%Y-%m-%d %H:%M:%S'), 'action':'sign_out'})
                    # sum up the attendances' durations
                    ldt = None
                    for att in attendences:
                        dt = datetime.strptime(att['name'], '%Y-%m-%d %H:%M:%S')
                        if ldt and att['action'] == 'sign_out':
                            if dt.date() > ldt.date():
                                dt = ldt
                            wh += (float((dt - ldt).seconds)/60/60)
                        else:
                            ldt = dt
                    total_wh += wh
                    wh = hour2str(wh)
                    wh_list.append(wh)
                    today, tomor = tomor, tomor + one_day
                return wh_list,wh_name, hour2str(total_wh)

report_sxw.report_sxw('report.hr.attendance.bymonth.webkit', 'hr.employee', 'addons/hr_attendance_webkit/report/attendance_by_month.mako', parser=attendance_by_month, header='internal')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

