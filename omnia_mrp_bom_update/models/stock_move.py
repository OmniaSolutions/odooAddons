# -*- coding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, ERP-PLM-CAD Open Source Solution
#    Copyright (C) 2011-2019 https://wwww.omniasolutions.website
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
#    along with this prograIf not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
'''
Created on Apr 6, 2019

@author: mboscolo
'''


import logging
import datetime
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
from odoo.exceptions import UserError
from datetime import timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class StockMove(models.Model):
    _name = "stock.move"
    _inherit = ['stock.move']
    
    @api.model
    def generate_mrp_line(self, mrp_production_id, mrp_bom_line_ids):
        bom_line_ids = [line.id for line in mrp_bom_line_ids]
        factor = mrp_production_id.product_uom_id._compute_quantity(mrp_production_id.product_qty, mrp_production_id.bom_id.product_uom_id) / mrp_production_id.bom_id.product_qty
        boms, exploded_lines = mrp_production_id.bom_id.explode(mrp_production_id.product_id, factor, picking_type=mrp_production_id.bom_id.picking_type_id)
        for bom_line_id, line_data in exploded_lines:
            if bom_line_id.id in bom_line_ids:
                mrp_production_id._onchange_move_raw()
                break
                #mrp_production_id._update_raw_moves(factor)
                #mrp_production_id._generate_raw_move(bom_line_id, line_data)
                #mrp_production_id._get_move_raw_values(self, product_id, product_uom_qty, product_uom, operation_id=False, bom_line=False):
        # Check for all draft moves whether they are mto or not
        mrp_production_id.move_raw_ids._adjust_procure_method()
        mrp_production_id.move_raw_ids._action_confirm()
    
    def _confirm_and_reverse(self):
        for stock_move in self:
            qty_done = stock_move.quantity_done
            raw_material_production_id = stock_move.raw_material_production_id
            stock_move.raw_material_production_id = False
            stock_move.production_id = False 
            if stock_move.state == 'draft':
                stock_move._action_confirm()
            new_stock_move = stock_move.copy({'raw_material_production_id': False,
                                              'production_id': False,
                                              'quantity_done': 0.0})
            location_id = new_stock_move.location_id
            location_dest_id = new_stock_move.location_dest_id
            new_stock_move.location_id = location_dest_id.id
            new_stock_move.location_dest_id = location_id.id
            new_stock_move.quantity_done += qty_done


    def confirm_and_reverse(self):
        for stock_move in self:
            if stock_move.quantity_done < stock_move.product_uom_qty:
                diffQty = stock_move.product_uom_qty - stock_move.quantity_done
                stock_move.quantity_done+=diffQty
            stock_move._confirm_and_reverse()                
            
            