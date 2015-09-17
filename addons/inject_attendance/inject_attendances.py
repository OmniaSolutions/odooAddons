'''
Created on Jun 18, 2015

@author: daniel
'''
from openerp.osv                        import osv, fields
from openerp.tools              import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate    import _
from datetime                   import datetime

class Hr_inject_attendance(osv.osv):
    _name = 'hr.attendance_forced'

    _columns = {
        'in_field'  : fields.datetime('In', required=True, select=1),
        'out_field' : fields.datetime('Out', required=True, select=1),
        'employee_id': fields.many2one('hr.employee', "Employee", required=True, select=True),

    }
 
    def accept_wizard(self, cr, uid, ids, context={}):
        for singleId in ids:
            brws = self.browse(cr, uid, singleId, context)
            dateIn = datetime.strptime(brws.in_field, DEFAULT_SERVER_DATETIME_FORMAT)
            dateTo = datetime.strptime(brws.out_field, DEFAULT_SERVER_DATETIME_FORMAT)
            employeeId = brws.employee_id.id
            attendanceObj = self.pool.get('hr.attendance')
            if self.verifySelectedDatesCompatibility(dateIn, dateTo):
                if self.verifyNoDatesInTheMiddle(cr, uid, dateIn, dateTo, employeeId, attendanceObj, context):
                    if self.verifyPreviousSignIsNotSignIn(cr, uid, dateIn, employeeId, attendanceObj, context):
                        if self.verifyNextSignIsNotSignOut(cr, uid, dateTo, employeeId, attendanceObj, context):
                            if self.createAttendances(cr, uid, dateIn, dateTo, employeeId, attendanceObj, context={}):
                                return True
        return False
        
    def createAttendances(self,cr, uid, dateIn, dateTo, employeeId, attendanceObj, context={}):
        inRes = attendanceObj.create(cr, uid, {
                                       'employee_id'    :employeeId,
                                       'action'         :'sign_in',
                                       'name'           :str(dateIn),
                                       'overwrite'      :True,
                                       })
        if inRes:
            outRes = attendanceObj.create(cr, uid, {
                                           'employee_id'    :employeeId,
                                           'action'         :'sign_out',
                                           'name'           :str(dateTo),
                                           'overwrite'      :True,
                                           })
            if outRes:          
                # I made all the writes here to avoid write attendance control
                # If i make inRes write before outRes create attendance control break the procedure
                attendanceObj.write(cr, uid, inRes, {'overwrite':False})
                attendanceObj.write(cr, uid, outRes, {'overwrite':False})
                return True
        raise osv.except_osv(_('Error!'),_("Some errors occurred during attendance creation"))

        
    def verifyPreviousSignIsNotSignIn(self, cr, uid, dateIn, employee_id, attendanceObj, context={}):
        alreadyWrittenAttendancesIds = attendanceObj.search(cr, uid, [('name','<=',str(dateIn))], limit=1, order='name DESC')
        for attId in alreadyWrittenAttendancesIds:
            attBrws = attendanceObj.browse(cr, uid, attId )
            if attBrws.action ==  'sign_out':
                return True
        if not alreadyWrittenAttendancesIds:
            return True
        raise osv.except_osv(_('Error!'),_("Previous employee sign is a sign_in, you can't set a sign_in again."))
    
    def verifyNextSignIsNotSignOut(self, cr, uid, dateTo, employee_id, attendanceObj, context={}):
        alreadyWrittenAttendancesIds = attendanceObj.search(cr, uid, [('name','>=',str(dateTo))], limit=1, order='name ASC')
        for attId in alreadyWrittenAttendancesIds:
            attBrws = attendanceObj.browse(cr, uid, attId )
            if attBrws.action ==  'sign_in':
                return True
        if not alreadyWrittenAttendancesIds:
            return True
        raise osv.except_osv(_('Error!'),_("Next employee sign is a sign_out, you can't set a sign_out again."))
        
    def verifyNoDatesInTheMiddle(self, cr, uid, dateIn, dateTo, employeeId, attendanceObj, context={}):
        alreadyWrittenAttendances = attendanceObj.search(cr, uid, [('name','>=',str(dateIn)),('name','<=',str(dateTo))])
        if not alreadyWrittenAttendances:
            return True
        raise osv.except_osv(_('Error!'),_("One or more dates are written inside the selected dates interval"))
        
    def verifySelectedDatesCompatibility(self, dateIn, dateTo):
        if dateIn>dateTo:
            raise osv.except_osv(_('Error!'),_("Selected dates can't be written, \n Sign In follows Sign Out"))
        return True
        
Hr_inject_attendance()

class Hr_attendance_avoid_control(osv.osv):
    _name = 'hr.attendance'
    _inherit = 'hr.attendance'
    _columns = {
                'overwrite' : fields.boolean('Overwrite'),
                }
    _defaults = {
                 'overwrite':False,
                 }
        
    def _altern_si_so(self, cr, uid, ids, context={}):
        for attId in ids:
            attBrws = self.browse(cr, uid, attId)
            if attBrws.overwrite:
                return True
        return super(Hr_attendance_avoid_control,self)._altern_si_so(cr, uid, ids, context)

    _constraints = [(_altern_si_so, 'Error ! Sign in (resp. Sign out) must follow Sign out (resp. Sign in)', ['action'])]

Hr_attendance_avoid_control()
    
    