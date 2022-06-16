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
Created on Dec 18, 2017

@author: daniel
'''

from odoo import models
from odoo import fields
from odoo import api
from odoo import _
import logging
import datetime


class StockMove(models.Model):

    _inherit = ['stock.move']

    mrp_original_move = fields.Char(_('Is genereted from orignin MO'))
    mrp_production_id = fields.Integer(string=_('Original Mrp Production id'),
                                       help="""source Mrp Production Subcontracting id""")
    mrp_workorder_id = fields.Integer(string=_('Original Mrp Work Order id'),
                                      help="""source Mrp Workorder Subcontracting id""")
    workorder_id = fields.Many2one('mrp.workorder', _('workorder'))
    purchase_order_line_subcontracting_id = fields.Integer(_('Original Purchase line Id'))
    subcontracting_source_stock_move_id = fields.Integer(_('Original Production ID'))
    subcontracting_move_id = fields.Integer(_('Original move id'))

    @api.model
    def moveQty(self, qty):
        if self.move_line_ids.qty_done == qty:
            self._action_done()
        else:
            if self.move_line_ids:
                total_qty = self.move_line_ids.qty_done - qty
                self.move_line_ids.qty_done = qty
                self._action_done()
                newMove = self.copy()
                newMove.quantity_done += total_qty
                newMove._action_confirm()
            else:
                self.quantity_done = qty
                if self.move_line_ids.qty_done == qty:
                    self._action_done()

    @api.model
    def subcontractingMove(self, from_location, to_location, product_id, qty):
        name = 'SUB: '
        # if self.picking_id.sub_workorder_id:
        #     woBrws = self.env['mrp.workorder'].search([('id', '=', self.picking_id.sub_workorder_id)])
        #     routingName = woBrws.operation_id.name
        #     phaseName = woBrws.name
        #     name += '[%s - %s] ' % (routingName, phaseName)
        name += product_id.display_name
        move_vals = {
            'name': name,
            'production_id': False,
            'mrp_workorder_id': False,
            'raw_material_production_id': False,
            'picking_id': False,
            'product_uom': product_id.uom_id.id,
            'location_id': from_location.id,
            'location_dest_id': to_location.id,
            'sale_line_id': False,
            'product_id': product_id.id,
            'product_uom_qty': qty,
            # 'subcontracting_move_id': source_move_id, Used only for deletion
            #'subcontracting_source_stock_move_id': source_move_id Used by write
            } 
        return self.create(move_vals)

    def subcontractFinishedProduct(self):
        '''
            Move finished product from subcontracting location to customer location to balance customer stock
        '''
        move_date = self.date
        subcontracting_location = self.env['stock.location'].getSubcontractingLocation()
        subcontract_finished_move = self.subcontractingMove(subcontracting_location, self.location_id, self.product_id, self.product_uom_qty)
        subcontract_finished_move.moveQty(self.quantity_done)  # Implicit call done action
        subcontract_finished_move.date = move_date
        if subcontract_finished_move.move_line_ids:
            subcontract_finished_move.move_line_ids.date = move_date
        return subcontract_finished_move

    def getRawSubcontractQty(self, production_id):
        out = []
        for moves in production_id.move_raw_ids:
            for move in moves:
                if move.mrp_production_id in (0, False):
                    prod_mo_qty = move.product_uom_qty
                    mo_qty = production_id.product_qty
                    qty = prod_mo_qty / mo_qty
                    out.append((move.product_id, qty))
        return out
        
    def subcontractRawProducts(self, subcontract_finished_move, objProduction):
        '''
            Generate raw materials subcontraction moves from partner location to subcontraction location to balance customer location
        '''
        if subcontract_finished_move.state == 'cancel':
            return
        move_date = subcontract_finished_move.date
        finished_qty = subcontract_finished_move.product_uom_qty
        to_subcontract = self.getRawSubcontractQty(objProduction)
        for product, unit_qty in to_subcontract:
            qty_to_subcontract = finished_qty * unit_qty
            raw_move = self.subcontractingMove(subcontract_finished_move.location_dest_id, subcontract_finished_move.location_id, product, qty_to_subcontract)
            raw_move.moveQty(qty_to_subcontract)  # Implicit call done action
            raw_move.date = self.date
            for lineBrws in raw_move.move_line_ids:
                lineBrws.date = move_date

    def _merge_moves(self, merge_into=False):
        to_merge = self.env[self._name]
        for move in self:
            if move.mrp_production_id or move.mrp_workorder_id:
                continue
            to_merge += move
        return super(StockMove, to_merge)._merge_moves(merge_into)
