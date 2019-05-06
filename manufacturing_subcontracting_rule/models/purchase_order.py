# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2010-2012 OpenERP s.a. (<http://openerp.com>).
#
#
#    Author : Smerghetto Daniel  (Omniasolutions)
#    mail:daniel.smerghetto@omniasolutions.eu
#    Copyright (c) 2014 Omniasolutions (http://www.omniasolutions.eu) 
#    All Right Reserved
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

'''
Created on Mar 27, 2018

@author: daniel
'''
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
import logging


class PurchaseOrder(models.Model):
    _name = "purchase.order"
    _inherit = ['purchase.order']

    production_external_id = fields.Many2one('mrp.production', string=_('External Production'))

    @api.multi
    def open_external_manufacturing(self):
        newContext = self.env.context.copy()
        manufacturingList = self.env['mrp.production'].browse()
        for purchaseLineBrws in self.order_line:
            manufacturingList = manufacturingList + purchaseLineBrws.production_external_id
        manufacturingIds = manufacturingList.ids
        return {
            'name': _("Manufacturing External"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'mrp.production',
            'type': 'ir.actions.act_window',
            'context': newContext,
            'domain': [('id', 'in', manufacturingIds)],
        }

    @api.depends('order_line.move_ids')
    def _compute_picking(self):
        super(PurchaseOrder, self)._compute_picking()
        for order in self:
            pickingsToAppend = self.env['stock.picking'].browse()
            for purchaseLineBrws in order.order_line:
                if purchaseLineBrws.production_external_id:
                    pickingsToAppend = pickingsToAppend + purchaseLineBrws.production_external_id.external_pickings
            order.picking_ids = order.picking_ids + pickingsToAppend
            order.picking_count = order.picking_count + len(pickingsToAppend)


class PurchaseOrderLine(models.Model):

    _name = "purchase.order.line"
    _inherit = ['purchase.order.line']

    production_external_id = fields.Many2one('mrp.production', string=_('External Production'))

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
