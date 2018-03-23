# -*- encoding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, Open Source Management Solution    
#    Copyright (C) 2010-2011 OmniaSolutions (<http://www.omniasolutions.eu>). All Rights Reserved
#    $Id$
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
Created on Mar 22, 2018

@author: dsmerghetto
'''

from odoo import models
from odoo import api
import logging


class SaleOrderExtension(models.Model):

    _name = "sale.order"
    _inherit = ['sale.order']
    
    @api.multi
    def action_confirm(self):
        if not self.checkIfModuleInstalled('omnia_sale_production_order'):
            self.checkLinesReorder()
        return super(SaleOrderExtension, self).action_confirm()

    @api.model
    def checkIfModuleInstalled(self, moduleName):
        moduleBrwsList = self.sudo().env['ir.module.module'].search([('name', '=', moduleName)])
        for modbrws in moduleBrwsList:
            if modbrws.state == 'installed':
                return True
        return False

    def checkLinesReorder(self):
        for lineBrws in self.order_line:
            prodBrws = lineBrws.product_id
            if prodBrws:
                tmplBrws = prodBrws.product_tmpl_id
                if tmplBrws.auto_reorder:
                    if not self.checkExistingReorderRule(prodBrws, self.warehouse_id):
                        self.createReorderRule(prodBrws, self.warehouse_id)
        
    def checkExistingReorderRule(self, prod_brws, warehouse):
        reorderRules = self.env['stock.warehouse.orderpoint'].search([
            ('product_id', '=', prod_brws.id),
            ('warehouse_id', '=', warehouse.id),
            ])
        if reorderRules:
            return True
        return False

    def createReorderRule(self, prod_brws, warehouse):
        logging.info('Creating reordering rule for product ID %r and warehouse ID %r' % (prod_brws.id, warehouse.id))
        toCreate = {
            'product_id': prod_brws.id,
            'warehouse_id': warehouse.id,
            'product_min_qty': 0,
            'product_max_qty': 0,
            'qty_multiple': 1,
            'location_id': warehouse.lot_stock_id.id,
            }
        wareHouseBrws = self.env['stock.warehouse.orderpoint'].create(toCreate)
        return wareHouseBrws
        