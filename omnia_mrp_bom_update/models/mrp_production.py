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


class MrpProduction(models.Model):
    _name = "mrp.production"
    _inherit = ['mrp.production']

    auto_bom_update = fields.Boolean(string=_('Automatically update mrp production from schedule'),
                                     help=_("""If this flag is up the bom the manufactory order in state ['confirmed', 'planned', 'progress'] as automatically updated by the server"""))
    
    def update_row_line_form_bom(self):
        for mrp_production_id in self.filtered(lambda x: x.state not in ['done', 'cancel']):
            if mrp_production_id.auto_bom_update:
                
                move_to_create = []
                for bom_line_id in mrp_production_id.bom_id.bom_line_ids:
                    addLine=True
                    for move_line_id in mrp_production_id.move_raw_ids:
                        if bom_line_id.product_id.id == move_line_id.product_id.id:
                            if move_line_id.state in ['draft', 'waiting', 'confirmed', 'assigned']:
                                if bom_line_id.product_qty * mrp_production_id.product_qty != move_line_id.product_uom_qty:
                                    reserve =False
                                    if move_line_id.state=='assigned':
                                        move_line_id._do_unreserve()
                                        reserve = True
                                    bomLineQty = bom_line_id.product_qty * mrp_production_id.product_qty
                                    move_line_id.product_uom_qty = bomLineQty
                                    move_line_id.should_consume_qty = bomLineQty
                                    if reserve:
                                        move_line_id._action_assign()
                            else:
                                mrp_production_id.message_post(body= """<b>Unable to update product: %r due to the move status in: %r</b></br>""" % (move_line_id.product_id.name, move_line_id.state))
                            addLine=False
                            break
                    if addLine:
                        move_to_create.append(bom_line_id)
                move_to_delete = []
                for move_line_id in mrp_production_id.move_raw_ids:
                    found = False
                    for bom_line_id in mrp_production_id.bom_id.bom_line_ids:
                        if bom_line_id.product_id.id == move_line_id.product_id.id:
                            found=True
                            break
                    if not found:
                        move_to_delete.append(move_line_id)
                for move_line_id in move_to_delete:
                    if move_line_id.state in ['draft', 'confirmed', 'assigned', 'waiting']:
                        if move_line_id.state=='assigned':
                            move_line_id._do_unreserve()
                        if move_line_id.quantity_done:
                            move_line_id.confirm_and_reverse()
                        else:
                            move_line_id._action_cancel()
                            move_line_id.unlink()
                    else:
                        mrp_production_id.message_post(body= """<b>Unable to delete product: %r due to the move status in: %r</b></br>""" % (move_line_id.product_id.name, move_line_id.state))
            if move_to_create:
                self.env['stock.move'].generate_mrp_line(mrp_production_id, move_to_create)
    
    @api.model
    def check_production_to_update(self):
        for mrp_production_id in self.search([('state', 'in', ['confirmed', 'planned', 'progress'] )]):
            mrp_production_id.update_row_line_form_bom()
            

            
            
            