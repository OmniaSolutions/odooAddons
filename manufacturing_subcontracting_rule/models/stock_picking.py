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
#    Copyright (c) 2018 Omniasolutions (http://www.omniasolutions.eu)
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
from odoo import api
from odoo import fields
from odoo import _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    external_production = fields.Many2one('mrp.production')
    pick_out = fields.Many2one('stock.picking', string=_('Reference Stock pick out'))
    sub_contracting_operation = fields.Selection([('open', _('Open external Production')),
                                                  ('close', _('Close external Production'))])
    sub_production_id = fields.Integer(string=_('Sub production Id'))
    sub_workorder_id = fields.Integer(string=_('Sub Workorder Id'))
    external_operation = fields.Selection([('normal', 'Normal'),
                                           ('parent', 'Parent'),
                                           ('operation', 'Operation')],
                                           default='normal',
                                           string=_('Produce it externally automatically as'),
                                           help="""Normal: Use the Parent object as Product for the Out Pickings and the raw material for the Out Picking
                                                   Parent: Use the Parent product for the In Out pickings
                                                   Operation: Use the Product that have the Operation assigned for the In Out pickings""")
    def isIncoming(self, objPick=None):
        if objPick is None:
            objPick = self
        return objPick.picking_type_code == 'incoming'

    def isOutGoing(self, objPick=None):
        if objPick is None:
            objPick = self
        return objPick.picking_type_code == 'outgoing'

    
    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        purchase_order_line = self.env['purchase.order.line']
        if self.isIncoming():
            objProduction = self.env['mrp.production'].search([('id', '=', self.sub_production_id)])
            if objProduction and objProduction.state == 'external':
                for stock_move_picking in self.move_lines:
                    if stock_move_picking.mrp_production_id == objProduction.id:
                        subcontract_finished_move = stock_move_picking.subcontractFinishedProduct()
                        stock_move_picking.subcontractRawProducts(subcontract_finished_move, objProduction)
                if objProduction.isPicksInDone():
                    objProduction.button_mark_done()
            production_recorded = False
            for stock_move_picking in self.move_lines:
                if stock_move_picking.workorder_id.id == self.sub_workorder_id and stock_move_picking.product_id.id == stock_move_picking.workorder_id.product_id.id:
                    stock_move_picking.subContractingProduce(stock_move_picking.workorder_id)
                if stock_move_picking.product_id.id == stock_move_picking.workorder_id.product_id.id and not production_recorded and stock_move_picking.workorder_id.state != 'done':
                    stock_move_picking.workorder_id.record_production()
                    production_recorded = True
            for stock_move_id in self.move_line_ids:
                mrp_workorder_id = stock_move_id.move_id.workorder_id
                if mrp_workorder_id:
                    mrp_workorder_id.qty_producing = stock_move_id.qty_done
                    mrp_workorder_id.record_production()
                    for purchese_order_line_id in self.env['purchase.order.line'].search([('workorder_external_id', '=', mrp_workorder_id.id)]):
                        purchese_order_line_id.qty_received += stock_move_id.qty_done
                    # TODO: mettere il tempo di lavorazione calcolato fra pick in e pick put
                if stock_move_id.move_id.purchase_order_line_subcontracting_id:
                    purchase_order_line_id = purchase_order_line.search([('id', '=', stock_move_id.move_id.purchase_order_line_subcontracting_id)])
                    purchase_order_line_id._compute_qty_received()
        return res

    
    def action_cancel(self):
        ref = super(StockPicking, self).action_cancel()
        for stock_picking in self:
            if stock_picking.isIncoming():
                objProduction = self.env['mrp.production'].search([('id', '=', stock_picking.sub_production_id)])
                if objProduction.state == 'external':
                    if objProduction.isPicksInDone():
                        objProduction.button_mark_done()
        return ref
