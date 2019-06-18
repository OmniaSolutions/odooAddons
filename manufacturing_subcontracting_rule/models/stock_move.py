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
    mrp_production_id = fields.Integer(_('Original mrp id'))
    purchase_order_line_subcontracting_id = fields.Integer(_('Original Purchase line Id'))
    subcontracting_move_id = fields.Integer(_('Original move id'))
    mrp_workorder_id = fields.Integer(string=_('Original Mrp Work Order id'),
                                      help="""source Mrp Workorder Subcontracting id""")

    @api.model
    def moveQty(self, qty):
        if self.product_qty == qty:
            self.action_done()
        else:
            total_qty = self.product_qty - qty
            newMove = self.copy()
            newMove.product_uom_qty += total_qty
            newMove.action_confirm()

    @api.model
    def subcontractingMove(self, from_location, to_location, source_id=False):
        name = 'SUB: '
        if self.picking_id.sub_workorder_id:
            woBrws = self.env['mrp.workorder'].search([('id', '=', self.picking_id.sub_workorder_id)])
            routingName = woBrws.production_id.routing_id.name
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
                                  'subcontracting_move_id': source_id})

    @api.multi
    def subContractingProduce(self, pick_in_product_qty):
        move_date = self.date
        subcontracting_location = self.env['stock.location'].getSubcontractiongLocation()
        production_move = self.subcontractingMove(subcontracting_location, self.location_id, self.id)
        production_move.product_uom_qty = pick_in_product_qty
        production_move.ordered_qty = pick_in_product_qty
        production_move.date = move_date
        return production_move

    @api.multi
    def write(self, value):
        for move in self:
            if 'quantity_done' in list(value.keys()):
                for subMove in self.search([('subcontracting_move_id', '=', move.id)]):
                    subMove.quantity_done = value['quantity_done']
        return super(StockMove, self).write(value)

    @api.model
    def create(self, vals):
        pick_id = vals.get('picking_id', False)
        if pick_id:
            pick = self.env['stock.picking'].browse(pick_id)
            if pick.external_production:
                vals['origin'] = pick.origin
        return super(StockMove, self).create(vals)
