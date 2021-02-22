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
        orderId = self.id
        if self.id.origin:
            orderId = self.id.origin
            sale_order = self.browse(orderId)
        else:
            sale_order = self
        old_ids = sale_order.order_line.ids
        new_ids = self.order_line.ids
        removed_ids = list(set(old_ids) - set(new_ids))
        omnia_ids = []
        for line in self.order_line:
            if line.parent_sale_line_needed or line.self_sale_line_needed:
                continue
            omnia_id = str(time.time())
            
            logging.warning(omnia_id)
            for needed_prod_id in line.product_id.needed_children_product_ids:
                line.self_sale_line_needed = omnia_id
                ret = self.update({'order_line': [(0,0, {'parent_sale_line_needed': omnia_id,
                                                         'product_id': needed_prod_id.id,
                                                         'product_uom_qty': line.product_uom_qty,
                                                         'name': needed_prod_id.display_name,
                                                         'is_child_line_needed': True})]})
                omnia_ids.append(omnia_id)
        for newLine in self.order_line.filtered(lambda x: x.parent_sale_line_needed in omnia_ids):
             newLine.product_id_change()
             newLine.price_unit=newLine.product_id.lst_price
             newLine._onchange_discount()  
        
        if removed_ids:
            refs = []
            for line in self.env['sale.order.line'].browse(removed_ids):
                idRef = line.self_sale_line_needed or line.parent_sale_line_needed
                if idRef:
                    refs.append(idRef)
            for ref in set(refs):
                for child_line in self.order_line:
                    if ref in [child_line.parent_sale_line_needed, child_line.self_sale_line_needed]:
                        self.update({'order_line': [(2, child_line.id, 0)]})
        for old_line in sale_order.order_line + self.order_line:
            if old_line.temporary_change:
                 old_line.temporary_change=False
        
        return {'type': 'ir.actions.client',
                'tag': 'reload' }


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    parent_product_id = fields.Many2one('product.product',
                                        string=_('Parent product')) 
    parent_sale_line_needed = fields.Char('Parent sale order line')
    self_sale_line_needed = fields.Char('Self Virtual Id')
    is_child_line_needed = fields.Boolean('Is child needed')
    temporary_change = fields.Boolean('TemporaryV Changed need update')
    
    @api.onchange('product_uom_qty')
    def changeQty(self):
        for line in self:
            if line.self_sale_line_needed:
                for child_line in self.env['sale.order.line'].search([('parent_sale_line_needed', '=', line.self_sale_line_needed),
                                                                      ('order_id', '=', line._origin.order_id.id)]):
                    child_line.product_uom_qty = line.product_uom_qty
                    child_line.temporary_change = True 
        return {'type': 'ir.actions.client',
                'tag': 'reload'}
    
    def getReletedLine(self):
        """
        support function to get the releted line
        """
        out = []
        
        for line in self:
            order_id = line.order_id.id 
            idRef = line.self_sale_line_needed or line.parent_sale_line_needed
            if idRef:
                out += self.search([('order_id', '=', order_id),
                                    '|', ('parent_sale_line_needed', '=', idRef),
                                         ('self_sale_line_needed', '=', idRef)])
        return out