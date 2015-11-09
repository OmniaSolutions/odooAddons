# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Camptocamp SA (http://www.camptocamp.com) 
# All Right Reserved
#
# Author : Nicolas Bessi (Camptocamp)
#
# Author : Smerghetto Daniel & Boscolo Matteo (Omniasolutions)
# Copyright (c) 2014 Omniasolutions (http://www.omniasolutions.eu) 
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

from openerp import report
import tempfile
import logging
import csv
from openerp import netsvc
from openerp import pooler
from openerp.report.report_sxw import *
from openerp import addons
from openerp import tools
from openerp.tools.translate import _
from openerp.osv.osv import except_osv

_logger = logging.getLogger(__name__)

def mako_template(text):
    """Build a Mako template.

    This template uses UTF-8 encoding
    """
    tmp_lookup  = TemplateLookup() #we need it in order to allow inclusion and inheritance
    return Template(text, input_encoding='utf-8', output_encoding='utf-8', lookup=tmp_lookup)

class CvsParser(report_sxw):
    """Custom class that use webkit to render HTML reports
       Code partially taken from report openoffice. Thanks guys :)
    """
    def __init__(self, name, table, rml=False, parser=False,header=True, store=False):
        self.parser_instance = False
        self.localcontext = {}
        report_sxw.__init__(self, name, table, rml, parser,
            header, store)

    def translate_call(self, src):
        """Translate String."""
        ir_translation = self.pool.get('ir.translation')
        name = self.tmpl and 'addons/' + self.tmpl or None
        res = ir_translation._get_source(self.parser_instance.cr, self.parser_instance.uid,
                                         name, 'report', self.parser_instance.localcontext.get('lang', 'en_US'), src)
        if res == src:
            # no translation defined, fallback on None (backward compatibility)
            res = ir_translation._get_source(self.parser_instance.cr, self.parser_instance.uid,
                                             None, 'report', self.parser_instance.localcontext.get('lang', 'en_US'), src)
        if not res :
            return src
        return res
    # override needed to keep the attachments storing procedure
    def create_single_pdf(self, cursor, uid, ids, data, report_xml, context=None):
        """generate the PDF"""
        from ir_report import REPORT_TYPE
        if context is None:
            context={}
        if report_xml.report_type != REPORT_TYPE:
            return super(CvsParser,self).create_single_pdf(cursor, uid, ids, data, report_xml, context=context)

        self.parser_instance = self.parser(cursor,
                                           uid,
                                            self.name2,
                                           context=context)
        self.pool = pooler.get_pool(cursor.dbname)
        objs = self.getObjects(cursor, uid, ids, context)
        self.parser_instance.set_context(objs, data, ids, report_xml.report_type)
        columneval=[col.name for col in report_xml.columns_ids]
        customFunction=report_xml['loop_custom_function']
        separator=report_xml['separator']
        csfile=tempfile.mkstemp(suffix=".csv")
        with open(csfile[1], 'wb') as csvfile:
            spamwriter=csv.writer(csvfile, 
                                  delimiter=str(separator),
                                  quotechar='|', 
                                  quoting=csv.QUOTE_MINIMAL)
            if len(objs)==0:
                #customFunction="organize_cvs(objects)"
                objs=eval(customFunction,self.parser_instance.localcontext)
            for o in objs:
                outRow=[]
                for toEval in columneval:
                    newContext={'o':o}
                    newContext.update(context)
                    newContext.update(self.parser_instance.localcontext)
                    value=eval(toEval,newContext)
                    if type(value)==float:
                        value=round(value,2)
                    if type(value)==str:
                        value=unicode(value)
                    outRow.append(value)
                spamwriter.writerow(outRow)
        csv_file = open(csfile[1], 'rb')
        csv_out = csv_file.read()
        csv_file.close()
        return (csv_out, 'csv')
    
    def create_source_pdf(self, cr, uid, ids, data, report_xml, context=None):
        return self.create_single_pdf(cr, uid, ids, data, report_xml, context)

    def create(self, cursor, uid, ids, data, context=None):
        """We override the create function in order to handle generator
           Code taken from report openoffice. Thanks guys :) """
        pool = pooler.get_pool(cursor.dbname)
        ir_obj = pool.get('ir.actions.report.xml')
        report_xml_ids = ir_obj.search(cursor, uid,
                [('report_name', '=', self.name[7:])], context=context)
        if report_xml_ids:

            report_xml = ir_obj.browse(cursor,
                                       uid,
                                       report_xml_ids[0],
                                       context=context)
            report_xml.report_rml = None
            report_xml.report_rml_content = None
            report_xml.report_sxw_content_data = None
            report_xml.report_sxw_content = None
            report_xml.report_sxw = None
        else:
            return super(CvsParser, self).create(cursor, uid, ids, data, context)
        from ir_report import REPORT_TYPE
        if report_xml.report_type != REPORT_TYPE :
            return super(CvsParser, self).create(cursor, uid, ids, data, context)
        result = self.create_source_pdf(cursor, uid, ids, data, report_xml, context)
        if not result:
            return (False,False)
        return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
