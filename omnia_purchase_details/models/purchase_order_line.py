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
from odoo import models, fields
from odoo import api

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    @api.multi
    @api.depends('product_qty','qty_received')
    def compute_delivery_state(self):
        for purcase_order_line_id in self:
            if purcase_order_line_id.product_qty > purcase_order_line_id.qty_received:
                purcase_order_line_id.delivery_state = 'not delivered'
            if purcase_order_line_id.product_qty == purcase_order_line_id.qty_received:
                purcase_order_line_id.delivery_state = 'delivered'
            if purcase_order_line_id.product_qty < purcase_order_line_id.qty_received:
                purcase_order_line_id.delivery_state = 'over delivered'
    
    delivery_state = fields.Char(compute=compute_delivery_state, store=True)
    
    
    
    
    
