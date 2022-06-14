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
    sub_production_id = fields.Integer(string=_('Sub production Id'))
    sub_workorder_id = fields.Integer(string=_('Sub Workorder Id'))
    dropship_pick = fields.Many2one('stock.picking', string=_('Dropship Pick'))

    def isIncoming(self, objPick=None):
        if objPick is None:
            objPick = self
        return objPick.picking_type_code == 'incoming'

    def isOutGoing(self, objPick=None):
        if objPick is None:
            objPick = self
        return objPick.picking_type_code == 'outgoing'

    def isDropship(self):
        dropship_type = self.env.ref('stock_dropshipping.picking_type_dropship')
        if self.picking_type_id == dropship_type:
            return True
        return False

    def checkDropship(self):
        def recursion(pick):
            previous_dropship = self.search([('dropship_pick', '=', pick.id)], limit=1)
            if not previous_dropship:
                return pick
            return recursion(previous_dropship)
        return recursion(self)

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        if isinstance(res, dict) and res.get('type', '') == 'ir.actions.act_window':
            return res
        if self.isIncoming() and not self.isDropship():
            objProduction = self.env['mrp.production'].search([('id', '=', self.sub_production_id)])
            if objProduction and objProduction.state == 'external':
                wh_out_dropship = self.checkDropship()
                if wh_out_dropship == self:
                    for stock_move_picking in self.move_lines:
                        if stock_move_picking.mrp_production_id == objProduction.id:
                            subcontract_finished_move = stock_move_picking.subcontractFinishedProduct()
                            stock_move_picking.subcontractRawProducts(subcontract_finished_move, objProduction)
                else:
                    first_dropship = wh_out_dropship.dropship_pick
                    for stock_move_picking in first_dropship.move_lines:
                        subcontract_finished_move = stock_move_picking.subcontractFinishedProduct()
                    for stock_move_picking in wh_out_dropship.move_lines:
                        stock_move_picking.subcontractRawProducts(subcontract_finished_move, objProduction)
                    self.recomputePurchaseQty(wh_out_dropship)
                    self.recomputePurchaseQty(first_dropship)
                if objProduction.isPicksInDone():
                    objProduction.state = 'done'
            production_recorded = False
            for stock_move_picking in self.move_lines:
                if stock_move_picking.product_id.id == stock_move_picking.workorder_id.product_id.id and not production_recorded and stock_move_picking.workorder_id.state != 'done':
                    before_state = objProduction.state
                    stock_move_picking.workorder_id.button_finish()
                    production_recorded = True
                    objProduction.state = before_state
            self.recomputePurchaseQty(self)
            self.cancel_other_partners_picks(self.partner_id, self.sub_production_id)
        return res

    def recomputePurchaseQty(self, pick):
        purchase_order_line = self.env['purchase.order.line']
        for stock_move_id in pick.move_line_ids:
            if stock_move_id.move_id.purchase_order_line_subcontracting_id:
                purchase_order_line_id = purchase_order_line.search([('id', '=', stock_move_id.move_id.purchase_order_line_subcontracting_id)])
                purchase_order_line_id._compute_qty_received()
        
    def cancel_other_partners_picks(self, partner_id, production_id):
        if production_id:
            if self.checkDropship() == self:
                purchase_order = self.env['purchase.order']
                objProduction = self.env['mrp.production'].search([('id', '=', production_id)])
                ext_pickings = objProduction.getExtPickIds()
                ext_purchase = objProduction._getExtPurchase()
                for picking_id in ext_pickings:
                    if picking_id.partner_id != partner_id:
                        picking_id.action_cancel()
                for purchase_order_id in purchase_order.browse(ext_purchase):
                    if purchase_order_id.partner_id != partner_id:
                        purchase_order_id.button_cancel()
    
