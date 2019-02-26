##############################################################################
#
#    OmniaSolutions, Your own solutions
#    Copyright (C) 01/mar/2018 OmniaSolutions (<http://www.omniasolutions.eu>). All Rights Reserved
#    info@omniasolutions.eu
#
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
Created on 01/mar/2015

@author: mboscolo
'''
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
import logging


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    @api.multi
    def _prepare_stock_moves(self, picking):
        move_lines = super(PurchaseOrderLine, self)._prepare_stock_moves(picking)
        for moveLineVals in move_lines:
            purchase_line_id = moveLineVals.get('purchase_line_id', False)
            if purchase_line_id:
                purchaseLine = self.browse(purchase_line_id)
                account = purchaseLine.account_analytic_id
                if account:
                    purchase_location = account.purchase_location
                    if purchase_location:
                        moveLineVals['location_dest_id'] = purchase_location.id
        return move_lines
        
