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


class StockMove(models.Model):

    _inherit = ['stock.move']

    def subcontractRawProducts(self, subcontract_finished_move, objProduction):
        '''
            Generate raw materials subcontraction moves from partner location to subcontraction location to balance customer location
        '''
        bom_line = self.env['mrp.bom.line']
        if subcontract_finished_move.state == 'cancel':
            return
        if subcontract_finished_move.product_id.row_material:
            move_date = subcontract_finished_move.date
            finished_qty = subcontract_finished_move.product_uom_qty
            x_len = bom_line.computeXLenghtByProduct(subcontract_finished_move.product_id)
            y_len = bom_line.computeYLenghtByProduct(subcontract_finished_move.product_id)
            product_uom_qty = bom_line.computeTotalQty(x_len, y_len, finished_qty)
            raw_move = self.subcontractingMove(subcontract_finished_move.location_dest_id, subcontract_finished_move.location_id, subcontract_finished_move.product_id.row_material, product_uom_qty)
            raw_move.moveQty(product_uom_qty)  # Implicit call done action
            raw_move.date = self.date
            for lineBrws in raw_move.move_line_ids:
                lineBrws.date = move_date
        else:
            return super(StockMove, self).subcontractRawProducts(subcontract_finished_move, objProduction)
