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
import logging
import datetime
from datetime import timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class MrpProduction(models.Model):

    _name = "mrp.production"
    _inherit = ['mrp.production']

    state = fields.Selection(selection_add=[('external', 'External Production')])
    external_partner = fields.Many2one('res.partner', string='External Partner')
    purchase_external_id = fields.Many2one('purchase.order', string='External Purchase')
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

    @api.multi
    def open_external_purchase(self):
        newContext = self.env.context.copy()
        manufacturingIds = []
        if self.purchase_external_id:
            manufacturingIds = [self.purchase_external_id.id]
        else:
            manObjs = self.env['purchase.order'].search([('manu_external_id', '=', self.id)])
            if manObjs:
                manufacturingIds = manObjs.ids
        newContext['default_manu_external_id'] = self.id
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
        picking_ids = self.env['stock.picking'].search([('sub_production_id', '=', self.id)])
        return {
            'name': _("Purchase External"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', picking_ids.ids)],
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

    def createTmpStockMove(self, sourceMoveObj, location_source_id, location_dest_id):
        tmpMoveObj = self.env["stock.tmp_move"]
        return tmpMoveObj.create({
            'name': sourceMoveObj.name,
            'company_id': sourceMoveObj.company_id.id,
            'product_id': sourceMoveObj.product_id.id,
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
            'date_expected': sourceMoveObj.date_expected,
            'mrp_original_move': False})

    def copyAndCleanLines(self, brwsList, location_dest_id, location_source_id):
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
            return locationObj.with_context({'lang': 'en_US'}).search([
                ('usage', '=', 'supplier'),
                ('name', '=', 'Vendors')])

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
    def button_produce_externally(self):
        values = {}
        location = self.routing_id.location_id.id
        partner = self.routing_id.location_id.partner_id or self.bom_id.external_partner
        if not partner:
            partner = self.env['res.partner'].search([], limit=1)
        if not location:
            location = self.getSupplierLocation()
        location = self.checkCreatePartnerWarehouse(partner)
        values['external_partner'] = partner.id
        values['move_raw_ids'] = [(6, 0, self.copyAndCleanLines(self.move_raw_ids, location.id, self.location_src_id.id))]
        values['move_finished_ids'] = [(6, 0, self.copyAndCleanLines(self.move_finished_ids, self.location_src_id.id, location.id))]
        values['consume_product_id'] = self.product_id.id
        values['consume_bom_id'] = self.bom_id.id
        values['external_warehouse_id'] = self.location_src_id.get_warehouse().id
        values['external_location_id'] = location.id
        values['partner_id'] = self.external_partner
        values['request_date'] = datetime.datetime.now()
        obj_id = self.env['mrp.production.externally.wizard'].create(values)
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

    @api.multi
    def button_cancel_produce_externally(self):
        stockPickingObj = self.env['stock.picking']
        for manOrderBrws in self:
            stockPickList = stockPickingObj.search([('origin', '=', manOrderBrws.name)])
            for pickBrws in stockPickList:
                pickBrws.move_lines.unlink()
                pickBrws.action_cancel()
                pickBrws.unlink()
            manOrderBrws.write({'state': 'confirmed'})
            for move_line in manOrderBrws.move_raw_ids + manOrderBrws.move_finished_ids:
                if move_line.mrp_original_move is False:
                    move_line._action_cancel()
                if move_line.state in ('draft', 'cancel'):
                    if move_line.mrp_original_move:
                        move_line.state = move_line.mrp_original_move
                    else:
                        move_line.unlink()

    def checkCreateReorderRule(self, prodBrws, warehouse):
        if not self.checkExistingReorderRule(prodBrws, warehouse):
            self.createReorderRule(prodBrws, warehouse)

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
