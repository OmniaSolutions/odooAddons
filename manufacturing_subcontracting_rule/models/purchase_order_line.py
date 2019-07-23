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

    _name = "purchase.order.line"
    _inherit = ['purchase.order.line']

    production_external_id = fields.Many2one('mrp.production', string=_('External Production'))
    workorder_external_id = fields.Many2one('mrp.workorder', string=_('External Workorder'))

    @api.depends('order_id.state', 'move_ids.state')
    def _compute_qty_received(self):
        super(PurchaseOrderLine, self)._compute_qty_received()
        orders = []
        incoming_picks = []
        for line in self:
            orders.append(line.order_id)
            for pick in line.order_id.picking_ids:
                if pick.isIncoming(pick):
                    incoming_picks.append(pick)
        incoming_picks = list(set(incoming_picks))
        logging.info('Incoming pickings %r' % (incoming_picks))
        for line in self:
            bom = line.production_external_id.bom_id
            if line.production_external_id and bom:
                logging.info('External production + BOM found')
                correct_product = bom.product_id
                if not correct_product:
                    correct_product = bom.product_tmpl_id.product_variant_id
                if correct_product and bom.external_product:
                    logging.info('Extenal product in BOM found')
                    if bom.external_product.id == line.product_id.id:
                        total = 0
                        for pick in incoming_picks:
                            if line.production_external_id.id == pick.external_production.id:
                                for move in pick.move_lines:
                                    if move.product_id.id == correct_product.id:
                                        if move.state == 'done':
                                            if move.product_uom != line.product_uom:
                                                total += move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
                                            else:
                                                total += move.product_uom_qty
                        line.qty_received = total

    
    @api.multi
    def _prepare_stock_moves(self, picking):
        '''
            Fix due to change products in purchase order, Odoo will create stock moves but with wrong locations
        '''
        move_lines = super(PurchaseOrderLine, self)._prepare_stock_moves(picking)
        for moveLineVals in move_lines:
            location_id = False
            location_dest_id = False
            for move in self.move_ids:
                if move.purchase_order_line_subcontracting_id:
                    location_id = move.location_id.id
                    location_dest_id = move.location_dest_id.id
                    moveLineVals['product_id'] = move.product_id.id # Setup not "S" product
            if not location_id or not location_dest_id:
                picking_id = moveLineVals.get('picking_id', False)
                if picking_id:
                    pick = self.env['stock.picking'].browse(picking_id)
                    location_id = pick.location_id.id
                    location_dest_id = pick.location_dest_id.id
            if location_id:
                moveLineVals['location_id'] = location_id
            if location_dest_id:
                moveLineVals['location_dest_id'] = location_dest_id
        return move_lines
