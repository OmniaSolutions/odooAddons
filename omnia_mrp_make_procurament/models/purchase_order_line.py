# -*- coding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, ERP-PLM-CAD Open Source Solutions
#    Copyright (C) 2011-2021 https://OmniaSolutions.website
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
from _ast import If
'''
Created on 26 Oct 2021

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

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    omnia_mrp_orig_move = fields.Many2one("stock.move",
                                          copy=False,
                                          string=_("Original Move"))
    def _merge_in_existing_line(self, product_id, product_qty, product_uom, location_id, name, origin, values):
        """ This function purpose is to be override with the purpose to forbide _run_buy  method
        to merge a new po line in an existing one.
        """
        analitic_id = self.env.context.get('omnia_analytic_id')
        orig_move_id = self.env.context.get('omnia_orig_move_id')
        if analitic_id and orig_move_id:
            if self.account_analytic_id.id == analitic_id and \
                self.omnia_mrp_orig_move.id==orig_move_id:
                return True
            return False
        return True
    
    @api.model
    def create(self, vals):
        analytic_id = self.env.context.get('omnia_analytic_id')
        if analytic_id and 'account_analytic_id' in vals:
            vals['account_analytic_id'] = analytic_id
        orig_move_id = self.env.context.get('omnia_orig_move_id')
        if orig_move_id:
            vals['omnia_mrp_orig_move'] = orig_move_id
        if 'move_dest_ids' in vals:
            for _action, move_id in vals['move_dest_ids']:
                vals['omnia_mrp_orig_move'] = move_id
        orderLine = super(PurchaseOrderLine, self).create(vals)
        if 'omnia_mrp_orig_move' in vals:
            for move in self.env['stock.move'].search([('id','=', vals['omnia_mrp_orig_move'])]):
                if not move.purchase_order_id:
                    move.purchase_order_id = orderLine.order_id.id
                    move.purchase_line_id= orderLine.id
                if not move.created_purchase_line_id:
                    move.created_purchase_line_id = orderLine.id
        return orderLine
    
    