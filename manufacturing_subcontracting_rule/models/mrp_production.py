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

    @api.model
    def createStockMoveBom(self):
        """
            create line for the bom
        """
        stock_move_bomObj = self.env['stock.bom']
        for bom_line in self.bom_id.bom_line_ids:
            vals = {'source_product_id': self.product_id.id,
                    'raw_product_id': bom_line.product_id.id,
                    'quantity': bom_line.product_qty,
                    'mrp_production_id': self.id}
            stock_move_bomObj.create(vals)

    @api.model
    def getQuantToRemove(self, product_id, qty):
        product_id_id = product_id.id
        for stock_move in self.stock_bom_ids:
            if stock_move.raw_product_id == product_id_id:
                return stock_move.quantity * qty

    def _getDefaultPartner(self):
        for mrp_production in self:
            mrp_production.external_partner=False
            for sb_id in mrp_production.bom_id.subcontractor_ids:
                mrp_production.external_partner=sb_id.id
                break

    state = fields.Selection(selection_add=[('external', 'External Production')])
    stock_bom_ids = fields.One2many('stock.bom',
                                    'mrp_production_id',
                                    string='Stock Boms',
                                    ondelete="cascade")

    external_partner = fields.Many2one('res.partner',
                                       compute='_getDefaultPartner',
                                       string='Default External Partner',
                                       help="""This is a computed field in order to modifier it go to BOM -> Subcontracting -> Set Owner of the location
                                               if you do not see the Production Place Field, be sure to be part of group stock.group_adv_location""")

    purchase_external_id = fields.Many2one('purchase.order',
                                           string='External Purchase')
    purchase_external_count = fields.Integer('Number of external picking', compute='_getCountExtPurchase')
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
    external_pickings_count = fields.Integer('Number of external picking', compute='_getCountExtPick')

    def _getCountExtPick(self):
        for item in self:
            pick_ids = item.getExtPickIds()
            if pick_ids:
                item.external_pickings_count = len(pick_ids)
            else:
                item.external_pickings_count = 0

    def _getCountExtPurchase(self):
        for item in self:
            pick_ids = item._getExtPurchase()
            if pick_ids:
                item.purchase_external_count = len(pick_ids)
            else:
                item.purchase_external_count = 0
                
    def _getExtPurchase(self):
        manufacturingIds = []
        if self.purchase_external_id:
            manufacturingIds = [self.purchase_external_id.id]
        else:
            purchaseLines = self.env['purchase.order.line'].search([('production_external_id', '=', self.id)])
            purchaseList = self.env['purchase.order'].browse()
            for purchaseLineBrws in purchaseLines:
                purchaseList = purchaseList + purchaseLineBrws.order_id
            manufacturingIds = purchaseList.ids
        return manufacturingIds

    def open_external_purchase(self):
        return {
            'name': _("Purchase External"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'context': self.env.context.copy(),
            'domain': [('id', 'in', self._getExtPurchase())],
        }

    def getExtPickIds(self):
        srock_picking_ids = []
        for mrp_workorder_id in self.workorder_ids:
            srock_picking_ids.extend(mrp_workorder_id.getExternalPickings().ids)
        srock_picking_ids.extend(self.external_pickings.ids)
        return srock_picking_ids
    
    def open_external_pickings(self):
        return {
            'name': _("External Pickings"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'context': self.env.context.copy(),
            'domain': [('id', 'in', self.getExtPickIds())],
        }

    @api.model
    def isPicksInDone(self):
        isOut = False
        for stock_picking in self.external_pickings:
            if stock_picking.isIncoming():
                if stock_picking.state == 'cancel':
                    isOut = True
                    continue
                if stock_picking.state != 'done':
                    return False
                else:
                    isOut = True
        return isOut

    def getSupplierLocation(self):
        for lock in self.env['stock.location'].search([('usage', '=', 'supplier'),
                                                       ('active', '=', True),
                                                       ('company_id', '=', False)]):
            return lock.id
        return False

    def createTmpStockMove(self, sourceMoveObj, location_source_id=None, location_dest_id=None):
        tmpMoveObj = self.env["stock.tmp_move"]
        if not location_source_id:
            location_source_id = sourceMoveObj.location_id.id
        if not location_dest_id:
            location_dest_id = sourceMoveObj.location_dest_id.id
        product_product_id = sourceMoveObj.product_id.id
        return tmpMoveObj.create({
            'name': sourceMoveObj.name,
            'company_id': sourceMoveObj.company_id.id,
            'product_id': product_product_id,
            'product_uom_qty': sourceMoveObj.product_uom_qty,
            'location_id': location_source_id,
            'location_dest_id': location_dest_id,
            'partner_id': self.external_partner.id,
            'note': sourceMoveObj.note,
            'state': 'draft',
            'origin': sourceMoveObj.origin,
            'warehouse_id': self.location_src_id.get_warehouse().id,
            'production_id': self.id,
            'product_uom': sourceMoveObj.product_uom.id,
            'date_expected': sourceMoveObj.forecast_expected_date,
            'mrp_original_move': False,
            'workorder_id': sourceMoveObj.workorder_id.id,
            'mo_source_move': sourceMoveObj.id,
            })


    def copyAndCleanLines(self,
                          brwsList,
                          location_dest_id=None,
                          location_source_id=None,
                          isRawMove=False):
        outElems = []
        for elem in brwsList:
            outElems.append(self.createTmpStockMove(elem, location_source_id, location_dest_id).id)
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

    def button_produce_externally(self):
        values = self.get_wizard_value()
        values['consume_product_id'] = self.product_id.id
        values['consume_bom_id'] = self.bom_id.id
        obj_id = self.env['mrp.production.externally.wizard'].create(values)
        obj_id.create_vendors()
        obj_id._request_date()
        self.env.cr.commit()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production.externally.wizard',
            'view_mode': 'form,tree',
            'view_type': 'form',
            'res_id': obj_id.id,
            'context': {'wizard_id': obj_id.id},
            'target': 'new',
        }

    def button_cancel_produce_externally(self):
        stockPickingObj = self.env['stock.picking']
        purchaseOrderObj = self.env['purchase.order']
        for manOrderBrws in self:
            moves = self.env['stock.move']
            stockPickList = stockPickingObj.search([('origin', '=', manOrderBrws.name)])
            stockPickList += stockPickingObj.search([('sub_production_id', '=', manOrderBrws.id)])
            for pickBrws in list(set(stockPickList)):
                pickBrws.action_cancel()
                moves += pickBrws.move_lines
            manOrderBrws.write({'state': 'confirmed'})
            movesToCancel = self.env['stock.move'].search([('subcontracting_move_id', 'in', moves.ids)])
            movesToCancel += manOrderBrws.move_raw_ids + manOrderBrws.move_finished_ids
            for move_line in movesToCancel:
                if move_line.mrp_original_move is False:
                    move_line._action_cancel()
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

    def do_unreserve(self):
        for production in self:
            production.move_raw_ids.filtered(lambda x: x.state not in ('done', 'cancel'))._do_unreserve()
            if production.state == 'external':
                production.do_cancel_external_move()
        return True

    def do_cancel_external_move(self):
        for mrp_production in self:
            for move in mrp_production.move_raw_ids:
                if move.state not in ['done', 'cancel']:
                    logging.info("Unreserve Move %r" % move.name)
                    move._action_cancel()
            for move in mrp_production.finished_move_line_ids:
                if move.state not in ['done', 'cancel']:
                    move.unlink()

    @api.model
    def unreservePlanned(self):
        error = []
        for mrp_production in self.search([('state', 'in', ['external'])]):
            try:
                logging.info("Unreserve from production %r in state %r" % (mrp_production.name, mrp_production.state))
                mrp_production.button_unreserve()
                if mrp_production.state == 'external':
                    mrp_production.do_cancel_external_move()
            except Exception as ex:
                error.append("Manufactory %r Error %r " % (mrp_production.id, ex))
        for pick in self.env['stock.picking'].search([('external_production', '!=', False),
                                                      ('state', 'not in', ['cancel', 'done'])]):
            logging.info("Unreserve Pick %r" % pick.name)
            try:
                pick.do_unreserve()
            except Exception as ex:
                error.append("Unreserve pick %r Error %r " % (mrp_production.id, ex))
        return error

    def copy(self, default={}):
        if self.external_partner or self.purchase_external_id or self.external_pickings:
            default['move_raw_ids'] = []
            default['move_finished_ids'] = []
        ret = super(MrpProduction, self).copy(default=default)
        ret._create_update_move_finished()
        return ret


class StockBom(models.Model):
    _name = 'stock.bom'
    _description = 'Sub-Contracting Stock Bom'
    
    source_product_id = fields.Integer("Source Product id")
    raw_product_id = fields.Integer("Source Product id")
    quantity = fields.Float("Product Quantity")
    mrp_production_id = fields.Many2one('mrp.production',
                                        'Related Production')
