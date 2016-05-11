# -*- coding: utf-8 -*-
##############################################################################
#    
#
#    Author : Smerghetto Daniel (Omniasolutions)
#    mail:daniel.smerghetto@omniasolutions.eu
#    Copyright (c) 2014 Omniasolutions (http://www.omniasolutions.eu) 
#    All Right Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from datetime import datetime
from openerp.osv import orm, fields, osv
class Stock_picking(orm.Model):
    _inherit = 'stock.picking'
    _columns =  {     
                 'ddt_sequence':  fields.many2one('ir.sequence',string="DDT Sequence"),
    }

    def getLastDDtDate(self,cr,uid,brwseId):
        """
            get last ddt date from all ddt
        """
        
        sql="""SELECT ddt_number,ddt_date FROM STOCK_PICKING WHERE DDT_NUMBER IS NOT NULL AND ddt_sequence=%s ORDER BY DDT_DATE DESC LIMIT 1;""" %(brwseId)
        cr.execute(sql)
        results=cr.dictfetchall()
        for result in results:
            return datetime.strptime(result.get('ddt_date','2000-01-01'),'%Y-%m-%d')
        return datetime.strptime('2000-01-01','%Y-%m-%d')
        
    
    def button_ddt_number(self, cr, uid, ids, vals, context=None):
        
        for brwsPick in self.browse(cr,uid,ids,context=context):
            brwseId=brwsPick.ddt_sequence.id
            if brwseId==None:
                sql="""SELECT id FROM IR_SEQUENCE WHERE CODE ='stock.ddt';"""
                cr.execute(sql)
                brwseId=cr.dictfetchall()[0]['id']
            lastDDtDate=self.getLastDDtDate(cr,uid,brwseId)
            if brwsPick.ddt_date==False:
                dateTest=datetime.now()
                self.write(cr, uid, [brwsPick.id], {'ddt_date': str(dateTest.strftime('%Y-%m-%d'))})
            else:
                dateTest=datetime.strptime(brwsPick.ddt_date,'%Y-%m-%d')
            if brwsPick.ddt_number==False or len(str(brwsPick.ddt_number))==0:
                if lastDDtDate>dateTest:
                    raise osv.except_osv(('Error'),("Impossibile staccare il ddt data antecedente all'ultimo ddt"))
                
                if brwsPick.ddt_sequence:
                    code=brwsPick.ddt_sequence.code
                    number= self.pool.get('ir.sequence').get(cr, uid, code)
                else:
                    number= self.pool.get('ir.sequence').get(cr, uid, 'stock.ddt')
                self.write(cr, uid, [brwsPick.id], {'ddt_number':number})
        return True

Stock_picking()

class Stock_picking_out_omnia(orm.Model):
    _inherit = "ir.sequence"
    _columns =  {
        'use_for_ddt':  fields.boolean(string="Use for DDT"),
    }

Stock_picking_out_omnia()
