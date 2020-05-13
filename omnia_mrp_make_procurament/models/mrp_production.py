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
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round


class MrpProduction(models.Model):
    _inherit = ['mrp.production']

    @api.multi
    def pullFromStockVirtual(self):
        WH_STOCK_ID = 15
        internal_picking = self.env['stock.picking']
        for mrp_production_id in self:
            if mrp_production_id.location_src_id.id == WH_STOCK_ID:
                continue
            for lineBws in mrp_production_id.move_raw_ids:
                if lineBws.remaining_qty <= 0:
                    continue
                qtyOnProductionLocation = lineBws.product_id.with_context({'location': mrp_production_id.location_src_id.id}).virtual_available
                neededQty = lineBws.remaining_qty
                stockQty = lineBws.product_id.with_context({'location': WH_STOCK_ID}).virtual_available 
                qtyOlreadyInternalMove = 0.0
                for m in self.env['stock.move'].search([('internal_production_id','=', self.id), ('product_id','=', lineBws.product_id.id)]):
                    qtyOlreadyInternalMove += m.product_qty
                if qtyOlreadyInternalMove >= neededQty:
                    continue
                if stockQty > 0 and neededQty:
                    if neededQty > 0: # Qty not availabe on destination location
                        if not internal_picking:
                            origin = "%s : %s" % (mrp_production_id.name, mrp_production_id.origin)
                            internal_picking = self.createInternalPick(WH_STOCK_ID,
                                                                       mrp_production_id.location_src_id,
                                                                       origin=origin)
                        qty_ramained = stockQty - abs(neededQty)
                        if qty_ramained >= 0:
                            qty_to_move = abs(neededQty)
                        else:
                            qty_to_move = stockQty
                        self.createInternalMove(lineBws.product_id,
                                                internal_picking,
                                                qty_to_move)
            if internal_picking:
                internal_picking.action_confirm()
                internal_picking.action_assign()
                
    @api.multi
    def create_procuraments(self):
        production_to_call = []
        make_procurament = self.env['make.procurement']
        stock_warehouse_orderpoint = self.env['stock.warehouse.orderpoint']
        for mrp_production_id in self:
            source_location_id = mrp_production_id.location_src_id
            mrp_production_id.action_assign()
            mrp_production_id.pullFromStockVirtual()
            mrp_production_id.action_assign()
            for move_line_id in mrp_production_id.move_raw_ids:
                if move_line_id.state in ['cancel', 'done']:
                    continue
                qty_remaining = move_line_id.remaining_qty
                if qty_remaining==0:
                    continue
                proc_qty = move_line_id.getOmniaProcurementQty()
                if  proc_qty == move_line_id.product_qty:
                    continue
                if move_line_id.product_id.virtual_available>0:
                    continue
                op_product_virtual = float(move_line_id.product_id.virtual_available)        
                location_orderpoints = stock_warehouse_orderpoint.search([('product_id', 'in', move_line_id.product_id.ids),
                                                                          ('location_id','=', source_location_id.id)])
                for orderpoint in location_orderpoints:
                    if float_compare(op_product_virtual, orderpoint.product_min_qty, precision_rounding=orderpoint.product_uom.rounding) <= 0:
                        qty = max(orderpoint.product_min_qty, orderpoint.product_max_qty) - op_product_virtual
                        substract_quantity = location_orderpoints.subtract_procurements_from_orderpoints()
                        s_qty = substract_quantity[orderpoint.id]
                        qty -= s_qty
                        qty_remaining =  qty_remaining - proc_qty
                        if qty > 0 and qty_remaining > 0: # necessari
                            new_proc = make_procurament.create({
                               'qty': qty_remaining,
                               'product_id': move_line_id.product_id.id,
                               'product_tmpl_id': move_line_id.product_id.product_tmpl_id.id,
                               'uom_id': move_line_id.product_id.uom_id.id,
                               'warehouse_id': source_location_id.get_warehouse().id
                               })
                            ret = new_proc.make_procurement1(self.name)
                            is_production = ret.production_id
                            if is_production:
                                origin = "PROD: %s : %s " % (self.name, self.origin or '')
                            else:
                                origin = "ACQ: %s : %s " % (self.name, self.origin or '')
                            if ret.origin:
                                ret.origin = ret.origin + origin
                            else:
                                ret.origin = origin
                            if is_production:
                                production_to_call.append(ret.production_id)
                            ret.orderpoint_id = orderpoint.id
                            ret.omnia_move_id = move_line_id.id
                            ret.run()
                        
        for production_id in production_to_call:
            production_id.create_procuraments()
        