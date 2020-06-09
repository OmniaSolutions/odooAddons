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
Created on Jul 21, 2017

@author: daniel
'''
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
import datetime
from openerp import models
from openerp import api
from openerp import fields
from openerp import _
from openerp import SUPERUSER_ID


class ProcurementOrderOmnia(models.Model):
    _name = 'procurement.order.omnia'

    @api.multi
    def auto_reordering_rules_calculation(self, forceMrpBrws=[]):
        """Compute the commitment date"""
        mrpProdEnv = self.env['mrp.production']
        reorderRuleEnv = self.env['stock.warehouse.orderpoint']
        mrpProdOrders = []
        if forceMrpBrws and isinstance(forceMrpBrws, (list, tuple)):
            mrpProdOrders = forceMrpBrws
        else:
            mrpProdOrders = mrpProdEnv.search([
                ('state', 'in', ['confirmed'])
                ])
        for mrpOrderBrws in mrpProdOrders:
            for moveLineBrws in mrpOrderBrws.move_lines:
                prodBrws = moveLineBrws.product_id
                if prodBrws.purchase_ok:
                    reorderingRules = reorderRuleEnv.search([
                        ('product_id', '=', prodBrws.id),
                        ('location_id', '=', mrpOrderBrws.location_src_id.id)
                        ])
                    if not reorderingRules:
                        warehouse_id = self.getWarehouse(mrpOrderBrws.location_src_id)
                        self.createReorderingRules(prodBrws.id, mrpOrderBrws.location_src_id.id, warehouse_id)

    @api.multi
    def getWarehouse(self, locationBrowse):
        warehouseEnv = self.env['stock.warehouse']
        warehouseBrws = warehouseEnv.search([
            ('lot_stock_id', '=', locationBrowse.id)])
        if warehouseBrws:
            return warehouseBrws.id
        return False
        
    @api.multi
    def createReorderingRules(self, product_id, location_id, warehouse_id):
        reorderRuleEnv = self.env['stock.warehouse.orderpoint']
        toCreate = {
            'product_id': product_id,
            'location_id': location_id,
            'product_min_qty': 0,
            'product_max_qty': 0,
            'qty_multiple': 1,
            'lead_type': 'supplier',
            }
        if warehouse_id:
            toCreate['warehouse_id'] = warehouse_id
        reorderRuleEnv.create(toCreate)
   
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: