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
from odoo import fields
from odoo import api
from odoo import _
from odoo.exceptions import UserError
import logging
import datetime
from datetime import timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _workorders_create(self, bom, bom_data):
        mrp_workorder_ids = super(MrpProduction, self)._workorders_create(bom, bom_data)
        for mrp_workorder_id in mrp_workorder_ids:
            if mrp_workorder_id.operation_id.external_product:
                mrp_workorder_id.external_product = mrp_workorder_id.operation_id.external_product
            if mrp_workorder_id.operation_id.external_operation:
                ctx = self.env.context.copy()
                ctx.update({'active_model': 'mrp.workorder',
                            'active_ids': [mrp_workorder_id.id]})
                objWiz = mrp_workorder_id.createWizard()
                objWiz.with_context(ctx).button_produce_externally()
        return mrp_workorder_ids

    state = fields.Selection(selection_add=[('external', 'External Production')])
    move_raw_ids_external_prod = fields.One2many('stock.move',
                                                 'raw_material_production_id',
                                                 'Raw Materials External Production',
                                                 oldname='move_lines',
                                                 copy=False,
                                                 states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    move_finished_ids_external_prod = fields.One2many('stock.move',
                                                      'production_id',
                                                      'Finished Products External Production',
                                                      copy=False,
                                                      states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    external_pickings = fields.One2many('stock.picking', 'external_production', string='External Pikings')

    @api.multi
    def closeMO(self):
        for production_id in self:
            for raw_move in production_id.move_raw_ids:
                raw_move.quantity_done = raw_move.product_uom_qty   # Do not remove or material is not consumed
            for finish_move in production_id.move_finished_ids:
                finish_move.quantity_done = finish_move.product_uom_qty   # Do not remove or material is not consumed
            production_id.post_inventory()
            production_id.button_mark_done()

    @api.multi
    def button_produce_externally(self):
        values = self.get_wizard_value()
        obj_id = self.env['mrp.externally.wizard'].create(values)
        obj_id.create_vendors(self)
        self.env.cr.commit()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.externally.wizard',
            'view_mode': 'form,tree',
            'view_type': 'form',
            'res_id': obj_id.id,
            'context': {'wizard_id': obj_id.id},
            'target': 'new',
        }

    @api.multi
    def get_wizard_value(self):
        values = {}
        values['move_raw_ids'] = [(6, 0, self.generateTmpRawMoves())]
        values['move_finished_ids'] = [(6, 0, self.generateTmpFinishedMoves())]
        values['production_id'] = self.id
        values['request_date'] = datetime.datetime.now()
        return values

    def generateTmpFinishedMoves(self, location_source_id=None):
        outElems = []
        for stock_move_id in self.move_finished_ids:
            if stock_move_id.state in ['cancel', 'done']:
                continue
            newMove = self.createTmpStockMove(stock_move_id, location_source_id, self.location_src_id.id)
            newMove.source_production_move = stock_move_id.id
            newMove.production_id = False # Remove link with production order
            newMove.do_unreserve()
            newMove.state = 'draft'
            outElems.append(newMove.id)
        return outElems
        
    def generateTmpRawMoves(self, location_dest_id=None):
        outElems = []
        location_source_id = self.location_src_id.id
        for stock_move_id in self.move_raw_ids:
            if stock_move_id.state in ['cancel', 'done']:
                continue
            newMove = self.createTmpStockMove(stock_move_id, location_source_id, location_dest_id)
            newMove.source_production_move = stock_move_id.id
            newMove.do_unreserve()
            newMove.state = 'draft'
            newMove.raw_material_production_id = False # Remove link with production order
            newMove.operation_type = 'deliver_consume'
            outElems.append(newMove.id)
        return outElems

    def createTmpStockMove(self, sourceMoveObj, location_source_id=None, location_dest_id=None, unit_factor=1.0):
        tmpMoveObj = self.env["stock.tmp_move"]
        if not location_source_id:
            location_source_id = sourceMoveObj.location_id.id
        if not location_dest_id:
            location_dest_id = sourceMoveObj.location_dest_id.id
        source_move_vals = sourceMoveObj.read()
        for vals in source_move_vals:
            self.cleanReadVals(vals)
            return tmpMoveObj.create(vals)
        
    def cleanReadVals(self, vals):
        for key, val in vals.items():
            if isinstance(val, tuple) and len(val) == 2:
                vals[key] = val[0]
        if 'product_qty' in vals:
            del vals['product_qty']

    def checkCreatePartnerWarehouse(self, partnerBrws):
        if not partnerBrws:
            return False
        locationName = partnerBrws.name
        return self.createProductionLocation(locationName)

    def createProductionLocation(self, locationName):

        def getParentLocation():
            locations = locationObj.with_context({'lang': 'en_US'}).search([
                ('usage', '=', 'supplier'),
                ('name', '=', 'Vendors')])
            if locations:
                return locations[-1]
            raise UserError("No Vendor location defined")
        locationObj = self.env['stock.location']
        parentLoc = getParentLocation()
        vals = {
            'name': locationName,
            'location_id': parentLoc.id,
            'usage': 'internal'}
        locBrws = locationObj.search([
            ('name', '=', locationName),
            ('location_id', '=', parentLoc.id),
            ('usage', '=', 'internal')])
        if not locBrws:
            locBrws = locationObj.create(vals)
        return locBrws

    @api.multi
    def cancelPurchaseOrders(self):
        purchaseOrderObj = self.env['purchase.order']
        for purchese in purchaseOrderObj.search([('production_external_id', '=', self.id)]):
            purchese.button_cancel()
            purchese.unlink()

    @api.multi
    def cancelPickings(self):
        stockPickingObj = self.env['stock.picking']
        stockPickList = stockPickingObj.search([('origin', '=', self.name)])
        stockPickList += stockPickingObj.search([('sub_production_id', '=', self.id)])
        for pickBrws in list(set(stockPickList)):
            pickBrws.action_cancel()

    @api.multi
    def cancelRestoreMO(self):
        movesToCancel = self.move_raw_ids + self.move_finished_ids
        for move_line in movesToCancel:
            move_line.action_cancel()
            move_line.unlink()
        self._generate_moves()
        self.write({'state': 'confirmed'})

    @api.multi
    def button_cancel_produce_externally(self):
        for manOrderBrws in self:
            manOrderBrws.cancelPickings()
            manOrderBrws.cancelPurchaseOrders()
            manOrderBrws.cancelRestoreMO()


    def checkCreateReorderRule(self, prodBrws, warehouse):
        if warehouse:
            if not self.checkExistingReorderRule(prodBrws, warehouse):
                self.createReorderRule(prodBrws, warehouse)
        else:
            logging.warning("unable to create whrehouse")

    def checkExistingReorderRule(self, prod_brws, warehouse):
        reorderRules = self.env['stock.warehouse.orderpoint'].search([
            ('product_id', '=', prod_brws.id),
            ('warehouse_id', '=', warehouse.id)])
        if reorderRules:
            return True
        return False

    def createReorderRule(self, prod_brws, warehouse):
        logging.info('Creating reordering rule for product ID %r and warehouse ID %r' % (prod_brws.id, warehouse.id))
        toCreate = {
            'product_id': prod_brws.id,
            'warehouse_id': warehouse.id,
            'product_min_qty': 0,
            'product_max_qty': 0,
            'qty_multiple': 1,
            'location_id': warehouse.lot_stock_id.id}
        wareHouseBrws = self.env['stock.warehouse.orderpoint'].create(toCreate)
        return wareHouseBrws

    @api.model
    def isPicksInDone(self):
        isOut = False
        for stock_picking in self.external_pickings:
            if stock_picking.isIncoming(stock_picking):
                if stock_picking.state == 'cancel':
                    isOut = True
                    continue
                if stock_picking.state != 'done':
                    return False
                else:
                    isOut = True
        return isOut

    @api.multi
    def open_external_purchase(self):
        newContext = self.env.context.copy()
        manufacturingIds = []
        purchaseLines = self.env['purchase.order.line'].search([('production_external_id', '=', self.id)])
        purchaseList = self.env['purchase.order'].browse()
        for purchaseLineBrws in purchaseLines:
            purchaseList = purchaseList + purchaseLineBrws.order_id
        manufacturingIds = purchaseList.ids
        return {
            'name': _("Purchase External"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'context': newContext,
            'domain': [('id', 'in', manufacturingIds)],
        }

    @api.multi
    def open_external_pickings(self):
        newContext = self.env.context.copy()
        return {
            'name': _("External Pickings"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'context': newContext,
            'domain': [('id', 'in', self.external_pickings.ids)],
        }

#     @api.multi
#     def createSubcontractingMO(self, partner_location):
#         subcontracting_location = self.env['stock.location'].getSubcontractiongLocation()
#         for production in self:
#             for raw_move in production.move_raw_ids:
#                 new_sub_move = raw_move.subcontractingMove(partner_location, subcontracting_location, raw_move.id)
#                 new_sub_move.action_done()
#             for finish_move in production.move_finished_ids:
#                 new_sub_move = finish_move.subcontractingMove(subcontracting_location, partner_location, finish_move.id)
#                 new_sub_move.action_done()

#     @api.multi
#     def createSubcontractingMO(self):
#         subcontracting_location = self.env['stock.location'].getSubcontractiongLocation()
#         for pickIn in self:
#             finish_moves = pickIn.move_lines
#             for finish_move in finish_moves:
#                 new_sub_move = finish_move.subcontractingMove(subcontracting_location, finish_move.location_id, finish_move.id)
#                 new_sub_move.action_done()
#                 new_sub_move.date = finish_move.date
#             pick_out = pickIn.pick_out
#             if pick_out:
#                 for raw_line in pick_out.move_lines:
#                     moveQty = raw_line.quantity_done * raw_line.unit_factor
#                     raw_move = raw_line.subcontractingMove(raw_line.location_dest_id, subcontracting_location, self.id)
#                     raw_move.ordered_qty = moveQty
#                     raw_move.product_uom_qty = moveQty
#                     raw_move.action_done()
#                     raw_move.date = raw_line.date

    @api.multi
    def updateQtytoProduce(self, new_qty):
        for raw_id in self.move_raw_ids:
            expected_qty = new_qty * raw_id.unit_factor
            if raw_id.state == 'done':
                new_move = raw_id.copy()
                new_move.product_uom_qty = expected_qty - new_move.product_uom_qty
                new_move.action_assign()
            else:
                raw_id.product_uom_qty = expected_qty
                raw_id.do_unreserve()
                raw_id.action_assign()

        for finish_id in self.move_finished_ids:
            if finish_id.product_id == self.product_id:
                if finish_id.state == 'done':
                    new_move = finish_id.copy()
                    new_move.product_uom_qty = new_qty - new_move.product_uom_qty
                    new_move.action_assign()
                else:
                    finish_id.product_uom_qty = new_qty
                    finish_id.do_unreserve()
                    finish_id.action_assign()
            else:
                expected_qty = new_qty * raw_id.unit_factor
                if finish_id.state == 'done':
                    new_move = finish_id.copy()
                    new_move.product_uom_qty = expected_qty - new_move.product_uom_qty
                    new_move.action_assign()
                else:
                    finish_id.product_uom_qty = expected_qty
                    finish_id.do_unreserve()
                    finish_id.action_assign()
        
        self.write({'product_qty': new_qty})

#         for mo_id in self:
#             product_qty = self.env['change.production.qty'].create({
#                 'mo_id': mo_id.id,
#                 'product_qty': new_qty,
#             })
#             ctx = self.env.context.copy()
#             ctx['skip_external_check'] = True
#             product_qty.with_context(ctx).change_prod_qty()

    @api.multi
    def produceQty(self, qty_to_produce):
        ctx = self.env.context.copy()
        for mo_id in self:
            ctx['active_id'] = mo_id.id
            ctx['active_ids'] = [ctx['active_id']]
            product_qty = self.env['mrp.product.produce'].with_context(ctx).create({
                'production_id': mo_id.id,
                'product_id': mo_id.product_id.id,
                'product_qty': qty_to_produce,
                'product_uom_id': mo_id.product_uom_id.id,
            })
            product_qty.do_produce()

    @api.model
    def create(self, vals):
        return super(MrpProduction, self).create(vals)

    @api.multi
    def write(self, vals):
        return super(MrpProduction, self).write(vals)


class MrpProductProduce(models.TransientModel):
    _inherit = "mrp.product.produce"
    
    @api.model
    def create(self, vals):
        return super(MrpProductProduce, self).create(vals)
