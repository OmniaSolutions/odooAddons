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

@author: daniel
'''

from odoo import models
from odoo import fields
from odoo import api
from odoo import _
import logging
import datetime


class MrpProductionExtension(models.Model):

    _name = "mrp.production"
    _inherit = ['mrp.production']

    @api.model
    @api.returns('self', lambda value:value.id)
    def create(self, vals):
        manOrderBrws = super(MrpProductionExtension, self).create(vals)
        rawProds = self.getRawProds(manOrderBrws)
        self.createReorderRules(manOrderBrws, rawProds)
        return manOrderBrws
        
    def getRawProds(self, manOrderBrws):
        prodList = []
        for lineBws in manOrderBrws.move_raw_ids:
            product_template = lineBws.product_id.product_tmpl_id
            if product_template.type=='product' and product_template.auto_reorder:
                prodList.append(lineBws.product_id)
        return prodList

    def createReorderRules(self, manOrderBrws, prodList):
        warehouse = manOrderBrws.location_src_id.get_warehouse()
        for prodBrws in prodList:
            if prodBrws:
                tmplBrws = prodBrws.product_tmpl_id
                if not self.checkExistingReorderRule(prodBrws, warehouse):
                    self.createReorderRule(prodBrws, warehouse)

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

    @api.multi
    def button_reorder_rule(self):
        for mrp_production_id in self:
            rawProds = self.getRawProds(mrp_production_id)
            self.createReorderRules(mrp_production_id, rawProds)
            
            
