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
#         if not self.env.context.get('skip_omnia_project'):
#             move_id = vals.get('move_id', False)
#             operation_id = vals.get('operation_id', False)
#             if move_id and operation_id:
#                 move = self.env['stock.move'].browse(move_id)
#                 move_location = move.location_dest_id
#                 if move.picking_id.isIncoming(move.picking_id):
#                     self.env['stock.pack.operation'].browse(operation_id).location_id = move_location
#                 elif move.picking_id.isOutGoing(move.picking_id):
#                     self.env['stock.pack.operation'].browse(operation_id).location_dest_id = move_location
        return super(StockMoveOperationLink, self).create(vals)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def do_new_transfer(self):
        return super(StockPicking, self.with_context({'skip_omnia_project': True})).do_new_transfer()
        
