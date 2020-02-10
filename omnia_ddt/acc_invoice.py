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
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
import logging


class Omnia_ddt_account_invoice(models.Model):

    _name = "account.invoice"
    _inherit = ['account.invoice']
    ddt_number_invoice = fields.One2many('stock.picking', 'invoice_id', 'DDT_number')

    @api.multi
    def recupera_fattura(self):
        idspicking = []
        objStckPkng = self.env.get('stock.picking')
        for ogg in self:
            if (ogg.origin != 'merged') and (ogg.origin is not False):     # acc invoice has value and not merged
                idspicking.extend(objStckPkng.search([('origin', '=', ogg.origin),
                                                      ('ddt_number', '!=', False),
                                                      ('invoice_id', '=', None),
                                                      ('use_for_ddt', '=', True)],
                                                     ).ids)
            elif ogg.origin == 'merged':                             # Used only in case of "account_invoice_merge_no_unlink" module
                for mergedInv in self.search([('merged_invoice_id', '=', ogg.id)]):
                    if mergedInv.origin:
                        listaddt = mergedInv.origin.split(",")
                        for oggddt in listaddt:
                            idspicking.extend(objStckPkng.search([('origin', '=', oggddt.strip()),
                                                                  ('ddt_number', '!=', False),
                                                                  ('invoice_id', '=', None),
                                                                  ('use_for_ddt', '=', True)],
                                                                 ).ids)
        for ddtId in idspicking:
            objStckPkng.write(ddtId, {'invoice_id': self.env.ids[0]})
        return True

Omnia_ddt_account_invoice()
