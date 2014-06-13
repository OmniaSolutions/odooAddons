# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Camptocamp SA (http://www.camptocamp.com) 
# All Right Reserved
#
# Author : Nicolas Bessi (Camptocamp)
#
# Author : Smerghetto Daniel & Boscolo Matteo (Omniasolutions)
# Copyright (c) 2014 Omniasolutiosn (http://www.omniasolutions.eu) 
# All Right Reserved
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
##############################################################################

from openerp.osv import fields, osv
from openerp import netsvc
from openerp.report.report_sxw import rml_parse
from csv_report import CvsParser


REPORT_TYPE='cvs'

def register_report(name, model, tmpl_path, parser=rml_parse):
    """Register the report into the services"""
    name = 'report.%s' % name
    if netsvc.Service._services.get(name, False):
        service = netsvc.Service._services[name]
        if isinstance(service, CvsParser):
            #already instantiated properly, skip it
            return
        if hasattr(service, 'parser'):
            parser = service.parser
        del netsvc.Service._services[name]
    CvsParser(name, model, tmpl_path, parser=parser)

class ReportCvsColumn(osv.osv):
    _name = 'cvs.report.column'
    _columns = {
                'name':fields.text('Column Name'),
                'report_id':fields.integer('report id',invisible='1')
                }
ReportCvsColumn()  

class ReportCSV(osv.osv):

    def __init__(self, pool, cr):
        super(ReportCSV, self).__init__(pool, cr)

    def register_all(self,cursor):
        value = super(ReportCSV, self).register_all(cursor)
        cursor.execute("SELECT * FROM ir_act_report_xml WHERE report_type = '%s'"%str(REPORT_TYPE))
        records = cursor.dictfetchall()
        for record in records:
            register_report(record['report_name'], record['model'], record['report_rml'])
        return value

    def unlink(self, cursor, user, ids, context=None):
        """Delete report and unregister it"""
        trans_obj = self.pool.get('ir.translation')
        trans_ids = trans_obj.search(
            cursor,
            user,
            [('type', '=', 'report'), ('res_id', 'in', ids)]
        )
        trans_obj.unlink(cursor, user, trans_ids)

        # Warning: we cannot unregister the services at the moment
        # because they are shared across databases. Calling a deleted
        # report will fail so it's ok.

        res = super(ReportCSV, self).unlink(
                                            cursor,
                                            user,
                                            ids,
                                            context
                                        )
        return res

    def create(self, cursor, user, vals, context=None):
        "Create report and register it"
        res = super(ReportCSV, self).create(cursor, user, vals, context)
        if vals.get('report_type','') == REPORT_TYPE:
            # I really look forward to virtual functions :S
            register_report(
                        vals['report_name'],
                        vals['model'],
                        vals.get('report_rml', False)
                        )
        return res

    def write(self, cr, uid, ids, vals, context=None):
        "Edit report and manage it registration"
        if isinstance(ids, (int, long)):
            ids = [ids,]
        for rep in self.browse(cr, uid, ids, context=context):
            if rep.report_type != REPORT_TYPE:
                continue
            if vals.get('report_name', False) and \
                vals['report_name'] != rep.report_name:
                report_name = vals['report_name']
            else:
                report_name = rep.report_name

            register_report(
                        report_name,
                        vals.get('model', rep.model),
                        vals.get('report_rml', rep.report_rml)
                        )
        res = super(ReportCSV, self).write(cr, uid, ids, vals, context)
        return res

    _name = 'ir.actions.report.xml'
    _inherit = 'ir.actions.report.xml'
    _columns = {
        'loop_custom_function':fields.text('Loop Custom Function'),
        'separator' : fields.char('Separator', size=1),
        'columns_ids': fields.one2many(
                                    'cvs.report.column',
                                    'report_id',
                                    'ReportCvsColumn'),
        
    }

ReportCSV()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
