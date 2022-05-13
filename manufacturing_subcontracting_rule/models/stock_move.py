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

    _name = "stock.move"
    _inherit = ['stock.move']

    mrp_original_move = fields.Char(_('Is genereted from orignin MO'))
    mrp_production_id = fields.Integer(string=_('Original Mrp Production id'),
                                       help="""source Mrp Production Subcontracting id""")
    mrp_workorder_id = fields.Integer(string=_('Original Mrp Work Order id'),
                                      help="""source Mrp Workorder Subcontracting id""")
    purchase_order_line_subcontracting_id = fields.Integer(_('Original Purchase line Id'))
    subcontracting_source_stock_move_id = fields.Integer(_('Original Production ID'))
    subcontracting_move_id = fields.Integer(_('Original move id'))
    operation_type = fields.Selection([
        ('deliver', _('Deliver')),
        ('consume', _('Consume')),
        ('deliver_consume', _('Deliver and Consume')),
        ],
        default='deliver_consume',
        help="""
Deliver:   Send to subcontractor location
Stock -> Subcontractor

Consume:   Consume from subcontractor location
Subcontractor -> Subcontract location

Deliver and Consume:  Send to subcontractor location + Consume from subcontractor location
Stock -> Subcontractor
Subcontractor -> Subcontract location
        """
    )

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
    def subcontractingMove(self, from_location, to_location, source_id=False):
        name = 'SUB: '
        if self.picking_id.sub_workorder_id:
            woBrws = self.env['mrp.workorder'].search([('id', '=', self.picking_id.sub_workorder_id)])
            routingName = woBrws.operation_id.name
            phaseName = woBrws.name
            name += '[%s - %s] ' % (routingName, phaseName)
        name += self.display_name
        return self.copy(default={'name': name,
                                  'location_id': from_location.id,
                                  'location_dest_id': to_location.id,
                                  'sale_line_id': False,
                                  'production_id': False,
                                  'raw_material_production_id': False,
                                  'picking_id': False,
                                  'subcontracting_move_id': source_id,
                                  'subcontracting_source_stock_move_id': source_id})

    @api.model
    def subContractingFilterRow(self, production_id, move_from_id, move_to, qty):
        # This Function must be overloaded in order to perform custom behaviour
        production_id = move_to.mrp_production_id
        workorder_id = move_to.mrp_workorder_id or move_to.workorder_id.id
        if not production_id:
            if not workorder_id:
                return 0, True
        moveQty = qty * (move_to.unit_factor or 1)
        return moveQty, False

    def subcontractFinishedProduct(self):
        '''
            Move finished product from subcontracting location to customer location to balance customer stock
        '''
        move_date = self.date
        subcontracting_location = self.env['stock.location'].getSubcontractiongLocation()
        subcontract_finished_move = self.subcontractingMove(subcontracting_location, self.location_id, self.id)
        subcontract_finished_move.moveQty(self.quantity_done)  # Implicit call done action
        subcontract_finished_move.date = move_date
        if subcontract_finished_move.move_line_ids:
            subcontract_finished_move.move_line_ids.date = move_date
        return subcontract_finished_move

    def getRelatedSucontractPickOut(self, objProduction):
        pick_out_subcontracting = self.picking_id.pick_out
        if not pick_out_subcontracting:
            for pick in objProduction.external_pickings:
                if pick.isOutGoing():
                    pick_out_subcontracting = pick
                    break
        return pick_out_subcontracting
        
    def subcontractRawProducts(self, subcontract_finished_move, objProduction):
        '''
            Generate raw materials subcontraction moves from partner location to subcontraction location to balance customer location
        '''
        if subcontract_finished_move.state == 'cancel':
            return
        subcontracting_location = self.env['stock.location'].getSubcontractiongLocation()
        move_date = subcontract_finished_move.date
        pick_out_subcontracting = self.getRelatedSucontractPickOut(objProduction)
        if not pick_out_subcontracting:
            logging.warning('Cannot find subcontracting picking out for production %r' % (objProduction.display_name))
            return
        for move in pick_out_subcontracting.move_lines:
            if move.operation_type in ['deliver_consume']:
                raw_move = move.subcontractingMove(move.location_dest_id, subcontracting_location, self.id)
                raw_move.moveQty(raw_move.product_qty)  # Implicit call done action
                raw_move.date = self.date
                for lineBrws in raw_move.move_line_ids:
                    lineBrws.date = move_date

    
    def subContractingProduce2(self, pick_in_product_qty):
        move_date = self.date
        subcontracting_location = self.env['stock.location'].getSubcontractiongLocation()
        production_move = self.subcontractingMove(subcontracting_location, self.location_id, self.id)
        production_move.product_uom_qty = pick_in_product_qty
        production_move.should_consume_qty = pick_in_product_qty
        production_move.date = move_date
        return production_move

    
    def write(self, value):
        for move in self:
            if 'quantity_done' in list(value.keys()):
                for subMove in self.search([('subcontracting_source_stock_move_id', '=', move.id)]):
                    subMove.quantity_done = value['quantity_done']
        return super(StockMove, self).write(value)

    @api.model
    def create(self, vals):
        return super(StockMove, self).create(vals)

    def update(self, values):
        return super(StockMove, self).update(values)