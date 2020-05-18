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
Created on May 8, 2019

@author: mboscolo
'''
import logging
import datetime
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
from odoo.exceptions import UserError
from datetime import timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    production_external_id = fields.Many2one('mrp.production', string=_('External Production'))
    workorder_external_id = fields.Many2one('mrp.workorder', string=_('External Workorder'))
    sub_move_line = fields.Many2one('stock.move', string=_('Subcontracting move ref'))

    @api.depends('order_id.state', 'move_ids.state')
    def _compute_qty_received(self):
        super(PurchaseOrderLine, self)._compute_qty_received()
        for line in self:
            prod_to_produce = self.env['product.product']
            s_product = self.env['product.product']
            if line.workorder_external_id:
                operation = line.workorder_external_id.operation_id.external_operation
                if operation == 'operation':
                    prod_to_produce = line.sub_move_line.product_id
                elif operation == 'parent':
                    prod_to_produce = line.workorder_external_id.product_id
                else:  # suppose normal
                    prod_to_produce = line.workorder_external_id.product_id
                s_product = line.workorder_external_id.external_product
                external_picks = line.workorder_external_id.getExternalPickings()
            elif line.production_external_id:
                prod_to_produce = line.production_external_id.product_id
                bom = line.production_external_id.bom_id
                if bom:
                    s_product = bom.external_product
                external_picks = line.production_external_id.external_pickings
            if prod_to_produce and s_product and external_picks:
                deliver_qty = 0
                if s_product == line.product_id:
                    for pick in external_picks:
                        if pick.isIncoming(pick):
                            for move in pick.move_lines:
                                if move.product_id == prod_to_produce:
                                    if move.state == 'done':
                                        if move.product_uom != line.product_uom:
                                            deliver_qty += move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
                                        else:
                                            deliver_qty += move.product_uom_qty
                line.qty_received = deliver_qty

