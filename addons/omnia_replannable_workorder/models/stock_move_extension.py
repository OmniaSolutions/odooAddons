# -*- encoding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, Open Source Management Solution
#    Copyright (C) 2010-2011 OmniaSolutions (<http://www.omniasolutions.eu>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

'''
Created on May 16, 2018

@author: daniel
'''

from odoo import models
from odoo import fields
from odoo import api
from odoo import _


class StockMoveExtension(models.Model):
    _name = 'stock.move'
    _inherit = 'stock.move'

    replanning_raw_moves = fields.Many2one('mrp.workorder', string=_('Replanning Raw Moves'))

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        createdMove = super(StockMoveExtension, self).create(vals)
        if createdMove.replanning_raw_moves:
            createdMove.workorder_id = createdMove.replanning_raw_moves  # To link to raw_moves
            createdMove.raw_material_production_id = createdMove.replanning_raw_moves.production_id  # To link to production order
        return createdMove

    @api.multi
    def write(self, vals):
        for move in self:
            msg = ''
            if move.replanning_raw_moves:  # Replanning change
                product_id = vals.get('product_id', None)
                if product_id:
                    newProdBrws = self.env['product.product'].browse(product_id)
                    msg = 'Changed product %s --> %s' % (self.product_id.name, newProdBrws.name)
                productUomQty = vals.get('product_uom_qty', None)
                if productUomQty:
                    prodBrws = self.product_id
                    if product_id:
                        prodBrws = newProdBrws
                    msg = msg + '     Changed product %s with quantity %s --> %s' % (prodBrws.name, self.product_uom_qty, productUomQty)
            if msg:
                move.replanning_raw_moves.message_post(body=msg)
        return super(StockMoveExtension, self).write(vals)

    @api.multi
    def open_related_workorder(self):
        self.ensure_one()
        if self.workorder_id:
            return {
                "type": "ir.actions.act_window",
                "res_model": "mrp.workorder",
                "views": [[False, "form"]],
                "res_id": self.workorder_id.id,
            }

    @api.multi
    def open_related_replannable_workorder(self):
        self.ensure_one()
        if self.replanning_raw_moves:
            return {
                "type": "ir.actions.act_window",
                "res_model": "mrp.workorder",
                "views": [[False, "form"]],
                "res_id": self.replanning_raw_moves.id,
            }
