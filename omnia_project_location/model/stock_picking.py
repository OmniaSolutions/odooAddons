##############################################################################
#
#    OmniaSolutions, Your own solutions
#    Copyright (C) 01/mar/2018 OmniaSolutions (<http://www.omniasolutions.eu>). All Rights Reserved
#    info@omniasolutions.eu
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
Created on 01/mar/2015

@author: mboscolo
'''
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
import logging


class StockMoveOperationLink(models.Model):
    _inherit = 'stock.move.operation.link'

    @api.model
    def create(self, vals):
        move_id = vals.get('move_id', False)
        operation_id = vals.get('operation_id', False)
        if move_id and operation_id:
            move_location = self.env['stock.move'].browse(move_id).location_dest_id
            self.env['stock.pack.operation'].browse(operation_id).location_dest_id = move_location
        return super(StockMoveOperationLink, self).create(vals)
#     def _prepare_pack_ops(self, quants, forced_qties):
#         res = super(StockPicking, self)._prepare_pack_ops(quants, forced_qties)
#         for pack_op in res:
#             pass
#         return res
        
