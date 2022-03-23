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


class MrpWorkorderExtension(models.Model):
    _name = 'mrp.workorder'
    _inherit = 'mrp.workorder'

    @api.depends('production_id.move_raw_ids', 'production_id')
    def get_raw_material(self):
        for mrp_workorder in self:
            out_raw = ""
            product_computed = []
            for stock_move in mrp_workorder.production_id.move_raw_ids:
                if stock_move.product_id.id in product_computed:
                    continue
                product_computed.append(stock_move.product_id.id)    
                if len(out_raw) > 0:
                    out_raw += ","
                out_raw += stock_move.product_id.display_name
            mrp_workorder.raw_material_name = out_raw

    raw_material_name = fields.Char("Raw material",
                                    compute="get_raw_material",
                                    store=True)

    def write(self, vals):
        ret = super(MrpWorkorderExtension, self).write(vals)
        if not vals.get('raw_material_name', False):
            self.get_raw_material()
        return ret
