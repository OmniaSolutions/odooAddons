##############################################################################
#
#    OmniaSolutions, Your own solutions
#    Copyright (C) 25/mag/2016 OmniaSolutions (<http://www.omniasolutions.eu>). All Rights Reserved
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
"""
Created on 25/mag/2016

@author: mboscolo
"""

from odoo import models
from odoo import fields
from odoo import api
from odoo import _


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'
    
    def get_wizard_value(self):
        tmpMoveObj = self.env["stock.tmp_move"]
        bom_line = self.env['mrp.bom.line']
        ret = super(MrpWorkorder, self).get_wizard_value()
        raw_move_ids = ret.get('move_raw_ids', [])
        for elem in raw_move_ids:
            raw_tmp_moves = tmpMoveObj.browse(elem[2])
            for raw_move in raw_tmp_moves:
                product_to_send = raw_move.product_id
                qty_to_send = raw_move.product_uom_qty
                if product_to_send.row_material:
                    x_len = bom_line.computeXLenghtByProduct(product_to_send)
                    y_len = bom_line.computeYLenghtByProduct(product_to_send)
                    raw_move.product_uom_qty = bom_line.computeTotalQty(x_len, y_len, qty_to_send)
                    raw_move.product_id = product_to_send.row_material
        return ret
        
        
