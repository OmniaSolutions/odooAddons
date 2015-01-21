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
import logging

class omnia_ddt_account_invoice(models.Model):
    
    _name = "account.invoice"
    _inherit = ['account.invoice']
    ddt_number_invoice = fields.One2many('stock.picking','invoice_id','DDT_number')

        
    def recupera_fattura(self,cr,uid,ids,context=None):   
        idspicking=[]
        objAccInv=self.pool.get('account.invoice')
        objStckPkng=self.pool.get('stock.picking')
        campoorigin=(objAccInv.browse(cr,uid,ids,context=context))
        for ogg in campoorigin:
            if (ogg.origin !='merged') and (ogg.origin!=False):
                idspicking.append(objStckPkng.search(cr,uid,[('name','=',ogg.origin),('ddt_number','!=',False)],context=context))

            if ogg.origin =='merged':
                idsmerge=objAccInv.search(cr,uid,[('merged_invoice_id','=',ogg.id)],context=context)
                fatturemergiate=self.browse(cr,uid,idsmerge,context=context)
                for oggetto in fatturemergiate:
                    if oggetto.origin:
                        listaddt=oggetto.origin.split(",")
                        for oggddt in listaddt:
                            idspicking.append(objStckPkng.search(cr,uid,[('name','=',oggddt.strip()),('ddt_number','!=',False)],context=context))
        
        for ddt in idspicking:
            if ddt:
                #idDdtLst=objStckPkng.search(cr,uid,[('id','=',ddt[0])])
                namesSrc=[str(objStckPkng.browse(cr,uid,ddt[0]).name)]
                for ogg in namesSrc:
                    SrcLst=objAccInv.search(cr,uid,[('origin','=',namesSrc)])
                if len(SrcLst)==0: 
                    self.write(cr,uid,ids,{'ddt_number_invoice':ddt[0]},context=context)
                else:
                    raise osv.except_osv(('Error'),("DDT gia' in uso")) 
                    #_logger=logging.getLogger(__name__)
                    #_logger.error("DDT already used")

        return True
omnia_ddt_account_invoice()