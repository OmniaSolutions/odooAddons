# -*- coding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, ERP-PLM-CAD Open Source Solutions
#    Copyright (C) 2011-2019 https://OmniaSolutions.website
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
#    along with this prograIf not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
'''
Created on 16 Dec, 2020

@author: dsmerghetto
'''
import logging
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
from odoo.exceptions import UserError
import time


class SaleOrder(models.Model):
    _inherit = 'sale.order'
  
    @api.onchange('order_line')
    def changeOrderLine(self):
        orderId = self.id.origin
        sale_order = self.browse(orderId)
        old_ids = sale_order.order_line.ids
        new_ids = self.order_line.ids
        removed_ids = list(set(old_ids) - set(new_ids))
        
        for line in self.order_line:
            print('[%r] %r' % (line.id, line.display_name))
            if line.parent_sale_line_needed or line.self_sale_line_needed:
                continue
            for needed_prod_id in line.product_id.needed_children_product_ids:
                omnia_id = str(time.time())
                line.self_sale_line_needed = omnia_id
                self.order_line = [(0,0, {
                        'parent_sale_line_needed': omnia_id,
                        'product_id': needed_prod_id.id,
                        'product_uom_qty': line.product_uom_qty,
                        'price_unit': needed_prod_id.lst_price,
                        'name': needed_prod_id.display_name,
                        'is_child_line_needed': True}
                    )]
        for line in self.order_line:
            print(line.parent_sale_line_needed)
            if line.id.ref == 0: # New
                line.product_id_change()
        
        if removed_ids:
            for line in self.env['sale.order.line'].browse(removed_ids):
                for child_line in self.env['sale.order.line'].search([('parent_sale_line_needed', '=', line.self_sale_line_needed)]):
                    self.update({'order_line': [(2, child_line.id, 0)]})


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    parent_product_id = fields.Many2one('product.product',
                                        string=_('Parent product')) 
    parent_sale_line_needed = fields.Char('Parent sale order line')
    self_sale_line_needed = fields.Char('Self Virtual Id')
    is_child_line_needed = fields.Boolean('Is child needed')
    
    @api.onchange('product_uom_qty')
    def changeQty(self):
        for line in self:
            if line.self_sale_line_needed:
                for child_line in self.env['sale.order.line'].search([('parent_sale_line_needed', '=', line.self_sale_line_needed)]):
                    child_line.product_uom_qty = line.product_uom_qty
