##############################################################################
#
#    OmniaSolutions, Your own solutions
#    Copyright (C) 10/lug/2013 OmniaSolutions (<http://www.omniasolutions.eu>). All Rights Reserved
#    info@omniasolutions.eu
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
'''    
Created on 10/lug/2013
@author: mboscolo
'''
from openerp import models, fields, api
from openerp.osv import osv
import logging

class Omnia_ddt_account_invoice(models.Model):
    
    _name = "account.invoice"
    _inherit = ['account.invoice']
    ddt_number_invoice = fields.One2many('stock.picking','invoice_id','DDT_number')

    def recupera_fattura(self,cr,uid,ids,context=None):   
        idspicking=[]
        objAccInv=self.pool.get('account.invoice')
        objStckPkng=self.pool.get('stock.picking')
        if ids:
            if isinstance(ids, int):
                ids = [ids]
            brwsObj = objAccInv.browse(cr,uid,ids,context=context)
            for ogg in brwsObj:
                if (ogg.origin !='merged') and (ogg.origin!=False):     # acc invoice has value and not merged
                    idspicking.extend(objStckPkng.search(cr,uid,[('name','=',ogg.origin),('ddt_number','!=',False),('invoice_id','=',None)],context=context))
                elif ogg.origin =='merged':                             # Used only in case of "account_invoice_merge_no_unlink" module
                    idsmerge=objAccInv.search(cr,uid,[('merged_invoice_id','=',ogg.id)],context=context)
                    mergedInvoices=self.browse(cr,uid,idsmerge,context=context)
                    for mergedInv in mergedInvoices:
                        if mergedInv.origin:
                            listaddt=mergedInv.origin.split(",")
                            for oggddt in listaddt:
                                idspicking.extend(objStckPkng.search(cr,uid,[('name','=',oggddt.strip()),('ddt_number','!=',False),('invoice_id','=',None)],context=context))
            for ddtId in idspicking:
                objStckPkng.write(cr, uid, ddtId, {'invoice_id':ids[0]})
        return True
        
Omnia_ddt_account_invoice()