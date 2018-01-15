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


class MrpProduction(models.Model):

    _name = "mrp.production"
    _inherit = ['mrp.production']

    state = fields.Selection(selection_add=[('external', 'External Production')])
    external_partner = fields.Many2one('res.partner', string='External Partner')

    @api.multi
    def button_produce_externally(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production.externally.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'views': [(False, 'form')],
            'target': 'new',
        }

    @api.multi
    def button_cancel_produce_externally(self):
        stockPickingObj = self.env['stock.picking']
        for manOrderBrws in self:
            stockPickList = stockPickingObj.search([('origin', '=', manOrderBrws.name)])
            for pickBrws in stockPickList:
                pickBrws.action_cancel()
            manOrderBrws.write({'state': 'confirmed'})


class MrpProductionWizard(models.TransientModel):

    _name = "mrp.production.externally.wizard"

    external_partner = fields.Many2one('res.partner', string='External Partner', required=True)

    @api.multi
    def button_produce_externally(self):
        model = self.env.context.get('active_model', '')
        objIds = self.env.context.get('active_ids', [])
        relObj = self.env[model]
        productionBrws = relObj.browse(objIds)
        productionBrws.write({'external_partner': self.external_partner.id,
                              'state': 'external'})
        self.createStockPickingIn(self.external_partner, productionBrws)
        self.createStockPickingOut(self.external_partner, productionBrws)
        productionBrws.button_unreserve()   # Needed to evaluate picking out move

    def getLocation(self):
        for lock in self.env['stock.location'].search([('usage', '=', 'supplier'),
                                                       ('active', '=', True),
                                                       ('company_id', '=', False)]):
            return lock.id
        return False

    def createStockPickingIn(self, partner, productionBrws):

        def getPickingType():
            warehouseId = productionBrws.picking_type_id.warehouse_id.id
            pickTypeObj = self.env['stock.picking.type']
            for pick in pickTypeObj.search([('code', '=', 'incoming'),
                                            ('active', '=', True),
                                            ('warehouse_id', '=', warehouseId)]):
                return pick.id
            return False

        stockObj = self.env['stock.picking']
        loc = self.getLocation()
        toCreate = {'partner_id': partner.id,
                    'location_id': loc,
                    'location_src_id': loc,
                    'location_dest_id': productionBrws.location_src_id.id,
                    'min_date': productionBrws.date_planned_start,
                    'move_type': 'direct',
                    'picking_type_id': getPickingType(),
                    'origin': productionBrws.name,
                    'move_lines': []}
        for productionLineBrws in productionBrws.move_finished_ids:
            toCreate['move_lines'].append(
                (0, False, {
                    'product_id': productionLineBrws.product_id.id,
                    'product_uom_qty': productionLineBrws.product_uom_qty,
                    'product_uom': productionLineBrws.product_uom.id,
                    'name': productionLineBrws.name,
                    'state': 'assigned'}))
        stockObj.create(toCreate)

    def createStockPickingOut(self, partner, productionBrws):
        def getPickingType():
            warehouseId = productionBrws.picking_type_id.warehouse_id.id
            pickTypeObj = self.env['stock.picking.type']
            for pick in pickTypeObj.search([('code', '=', 'outgoing'),
                                            ('active', '=', True),
                                            ('warehouse_id', '=', warehouseId)]):
                return pick.id
            return False

        stockObj = self.env['stock.picking']
        toCreate = {'partner_id': partner.id,
                    'location_id': productionBrws.location_src_id.id,
                    'location_dest_id': self.getLocation(),
                    'location_src_id': productionBrws.location_src_id.id,
                    'min_date': datetime.datetime.now(),
                    'move_type': 'direct',
                    'picking_type_id': getPickingType(),
                    'origin': productionBrws.name,
                    'move_lines': []}
        for productionLineBrws in productionBrws.move_raw_ids:
            toCreate['move_lines'].append(
                (0, False, {
                    'product_id': productionLineBrws.product_id.id,
                    'product_uom_qty': productionLineBrws.product_uom_qty,
                    'product_uom': productionLineBrws.product_uom.id,
                    'name': productionLineBrws.name,
                    'state': 'assigned'}))
        stockObj.create(toCreate)
