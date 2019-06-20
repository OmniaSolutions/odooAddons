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
    sub_contracting_operation = fields.Selection([('open', _('Open external Production')),
                                                  ('close', _('Close external Production'))])
    sub_production_id = fields.Integer(string=_('Sub production Id'))
    pick_out = fields.Many2one('stock.picking', string=_('Reference Stock pick out'))
    sub_workorder_id = fields.Integer(string=_('Sub Workorder Id'))

    @api.multi
    def do_new_transfer(self):
        res = super(StockPicking, self).do_new_transfer()
        if isinstance(res, dict) and 'view_mode' in res:    # In this case will be returned a wizard
            return res
        for objPick in self:
            self.commonSubcontracting(objPick)
        return res

    @api.multi
    def commonSubcontracting(self, objPick):
        if objPick.isIncoming(objPick):
            partner_location = objPick.location_id
            if objPick.sub_workorder_id:
                wo_id = objPick.env['mrp.workorder'].search([('id', '=', objPick.sub_workorder_id)])
                objPick.createSubcontractingWO(wo_id, partner_location)
            elif objPick.sub_production_id:
                production_id = objPick.env['mrp.production'].search([('id', '=', objPick.sub_production_id)])
                objPick.createSubcontractingMO(production_id, partner_location)

    @api.multi
    def createSubcontractingWO(self, wo_id, partner_location):
        target_product_id = wo_id.product_id
        production_id = wo_id.production_id
        if wo_id.operation_id.external_operation not in ['normal', False, '']:
            return 
        for pick_in in self:
            if self.isIncoming(pick_in):
                for move_id in pick_in.move_lines:
                    if move_id.product_id == target_product_id:
                        pick_in_product_qty = move_id.ordered_qty
                        self.subcontractFinished(pick_in, target_product_id, pick_in_product_qty)
                        self.subcontractRaw(production_id, pick_in_product_qty, partner_location)
                        total_received = pick_in.getPickRecursiveProductQty(target_product_id)
                        target_mo_qty = wo_id.qty_production
                        if total_received > target_mo_qty:
                            wo_id.updateQtytoProduce(total_received)    # Update WO and MO qty
                            if wo_id.isPicksInDone():
                                wo_id.closeWO()
                        elif total_received == target_mo_qty:
                            if wo_id.isPicksInDone():
                                wo_id.closeWO()
                        else:
                            if wo_id.isPicksInDone():
                                wo_id.closeWO()
                            else:
                                wo_id.produceQty(pick_in_product_qty)
                    else:
                        self.subcontractFinished(pick_in, move_id.product_id, move_id.product_uom_qty)
        self.updatePurchaseLines(production_id, wo_id)

    @api.multi
    def createSubcontractingMO(self, production_id, partner_location):
        target_product_id = production_id.product_id
        for pick_in in self:
            if self.isIncoming(pick_in):
                for move_id in pick_in.move_lines:
                    if move_id.product_id == target_product_id:
                        total_received = pick_in.getPickRecursiveProductQty(target_product_id)
                        target_mo_qty = production_id.product_qty
                        pick_in_product_qty = move_id.ordered_qty
                        self.subcontractFinished(pick_in, target_product_id, pick_in_product_qty)
                        self.subcontractRaw(production_id, pick_in_product_qty, partner_location)
                        if total_received > target_mo_qty:
                            production_id.updateQtytoProduce(total_received)
                            if production_id.isPicksInDone():
                                production_id.closeMO()
                        elif total_received == target_mo_qty:
                            if production_id.isPicksInDone():
                                production_id.closeMO()
                        if total_received < target_mo_qty:
                            production_id.produceQty(pick_in_product_qty)
                            production_id.post_inventory()
                    else:
                        self.subcontractFinished(pick_in, move_id.product_id, move_id.product_uom_qty)
        self.updatePurchaseLines(production_id)


    def updatePurchaseLines(self, production_id, workorder_id=False):
        purchase_line = self.env['purchase.order.line']
        to_search = [('production_external_id', '=', production_id.id)]
        if workorder_id:
            to_search = [('workorder_external_id', '=', workorder_id.id)]
        purchase_line_ids = purchase_line.search(to_search)
        for purchase_order_line in purchase_line_ids:
            purchase_order_line._compute_qty_received()
        
    def isIncoming(self, objPick):
        return objPick.picking_type_code == 'incoming'

    def isOutGoing(self, objPick):
        return objPick.picking_type_code == 'outgoing'

    def getStockQuant(self, stockQuantObj, lineId, prodBrws):
        quantsForProduct = stockQuantObj.search([
            ('location_id', '=', lineId),
            ('product_id', '=', prodBrws.id)])
        return quantsForProduct

    @api.multi
    def getPickRecursiveProductQty(self, target_product_id):
        out = 0
        for pick in self:
            for line in pick.move_lines:
                if line.product_id == target_product_id:
                    out += line.product_qty
            if pick.backorder_id:
                out += pick.backorder_id.getPickRecursiveProductQty(target_product_id)
        return out

    @api.multi
    def getPickProductQty(self, target_product_id):
        out = 0
        for pick in self:
            for line in pick.move_lines:
                if line.product_id == target_product_id:
                    out += line.product_qty
        return out

    def subcontractFinished(self, pick_in, target_product_id, pick_in_product_qty):
        for move_id in pick_in.move_lines:
            if move_id.product_id == target_product_id:
                new_sub_move = move_id.subContractingProduce(pick_in_product_qty)
                new_sub_move.action_done()
                return

    def subcontractRaw(self, production_id, finish_qty, partner_location):
        subcontracting_location = self.env['stock.location'].getSubcontractiongLocation()
        for raw_move in production_id.move_raw_ids:
            if raw_move.state not in ['done', 'cancel']:
                new_sub_move = raw_move.subcontractingMove(partner_location, subcontracting_location)
                moveQty = finish_qty * (raw_move.unit_factor or 1)
                new_sub_move.product_uom_qty = moveQty
                new_sub_move.ordered_qty = moveQty
                new_sub_move.action_done()

    @api.multi
    def action_cancel(self):
        key = 'skip_delete_recursion'
        context = self.env.context
        if not context.get(key):
            for pick_id in self:
                if pick_id.sub_workorder_id:
                    self.env['mrp.workorder'].browse(pick_id.sub_workorder_id).with_context({key: True}).button_cancel_produce_externally()
                    return
                elif pick_id.sub_production_id:
                    self.env['mrp.production'].browse(pick_id.sub_production_id).with_context({key: True}).button_cancel_produce_externally()
                    return
        return super(StockPicking, self).action_cancel()


class StockBackorderConfirmation(models.TransientModel):
    _name = 'stock.backorder.confirmation'
    _inherit = ['stock.backorder.confirmation']
     
    @api.multi
    def process(self):
        res = super(StockBackorderConfirmation, self).process()
        for objPick in self.pick_id:
            self.env['stock.picking'].commonSubcontracting(objPick)
        return res

    
class StockImmediateTransfer(models.TransientModel):
    _name = 'stock.immediate.transfer'
    _inherit = ['stock.immediate.transfer']

    @api.multi
    def process(self):
        res = super(StockImmediateTransfer, self).process()
        for objPick in self.pick_id:
            self.env['stock.picking'].commonSubcontracting(objPick)
        return res


class StockPackOperation(models.Model):
    _inherit = ['stock.pack.operation']

    @api.model
    def create(self, vals):
        res = super(StockPackOperation, self).create(vals)
        toWrite = {}
        if 'location_id' in vals:
            toWrite['location_id'] = vals['location_id']
        if 'location_dest_id' in vals:
            toWrite['location_dest_id'] = vals['location_dest_id']
        if toWrite:
            res.write(toWrite)
        return res

    @api.multi
    def write(self, vals):
        res = super(StockPackOperation, self).write(vals)
        return res