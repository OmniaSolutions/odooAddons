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

    _name = "mrp.production"
    _inherit = ['mrp.production']

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

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        return super(MrpProduction, self).create(vals)

    @api.multi
    def write(self, vals):
        return super(MrpProduction, self).write(vals)

    def getSupplierLocation(self):
        for lock in self.env['stock.location'].search([('usage', '=', 'supplier'),
                                                       ('active', '=', True),
                                                       ('company_id', '=', False)]):
            return lock.id
        return False

    def createTmpStockMove(self, sourceMoveObj, location_source_id=None, location_dest_id=None, unit_factor=1.0):
        tmpMoveObj = self.env["stock.tmp_move"]
        if not location_source_id:
            location_source_id = sourceMoveObj.location_id.id
        if not location_dest_id:
            location_dest_id = sourceMoveObj.location_dest_id.id
        return tmpMoveObj.create({
            'name': sourceMoveObj.name,
            'company_id': sourceMoveObj.company_id.id,
            'product_id': sourceMoveObj.product_id.id,
            'product_uom_qty': sourceMoveObj.product_uom_qty,
            'location_id': location_source_id,
            'location_dest_id': location_dest_id,
            'note': sourceMoveObj.note,
            'state': 'draft',
            'origin': sourceMoveObj.origin,
            'warehouse_id': self.location_src_id.get_warehouse().id,
            'production_id': self.id,
            'product_uom': sourceMoveObj.product_uom.id,
            'date_expected': sourceMoveObj.date_expected,
            'mrp_original_move': False,
            'workorder_id': sourceMoveObj.workorder_id.id,
            'unit_factor': sourceMoveObj.unit_factor})

    def copyAndCleanLines(self, brwsList, location_dest_id=None, location_source_id=None, isRawMove=False):
        outElems = []
        foundRawMoves = False
        evaluated = []
        for elem in brwsList:
            if isRawMove:   # Look for raw moves
                if elem.state == 'cancel':
                    continue
            prodId = elem.product_id.id
            
            if not isRawMove and prodId in evaluated:
                # Skip multiple finished lines if more than one workorder because are created too many lines
                continue
            foundRawMoves = True
            outElems.append(self.createTmpStockMove(elem, location_source_id, location_dest_id).id)
            evaluated.append(prodId)
        if not foundRawMoves and isRawMove:
            # Create automatically raw stock move containing finished product
            newMove = self.createTmpStockMove(elem, location_source_id, location_dest_id)
            newMove.product_id = self.product_id.id
            newMove.product_uom_qty = self.product_qty
            newMove.name = self.product_id.display_name
            newMove.note = ''
            newMove.product_uom = self.product_uom_id.id
            outElems.append(newMove.id)
        return outElems

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
    def get_wizard_value(self):
        values = {}
        values['move_raw_ids'] = [(6, 0, self.copyAndCleanLines(self.move_raw_ids,
                                                                location_source_id=self.location_src_id.id, 
                                                                isRawMove=True
                                                                ))]
        values['move_finished_ids'] = [(6, 0, self.copyAndCleanLines(self.move_finished_ids,
                                                                     location_dest_id=self.location_src_id.id,
                                                                     isRawMove=False))]
        values['production_id'] = self.id
        values['request_date'] = datetime.datetime.now()
        return values

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
    def button_cancel_produce_externally(self):
        stockPickingObj = self.env['stock.picking']
        purchaseOrderObj = self.env['purchase.order']
        for manOrderBrws in self:
            stockPickList = stockPickingObj.search([('origin', '=', manOrderBrws.name)])
            for pickBrws in stockPickList:
                pickBrws.move_lines.unlink()
                pickBrws.action_cancel()
                pickBrws.unlink()
            manOrderBrws.write({'state': 'confirmed'})
            for move_line in manOrderBrws.move_raw_ids + manOrderBrws.move_finished_ids:
                if move_line.mrp_original_move is False:
                    move_line.action_cancel()
                if move_line.state in ('draft', 'cancel'):
                    if move_line.mrp_original_move:
                        move_line.state = move_line.mrp_original_move
                    else:
                        move_line.unlink()
            for purchese in purchaseOrderObj.search([('production_external_id', '=', self.id)]):
                purchese.button_cancel()
                purchese.unlink()

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
