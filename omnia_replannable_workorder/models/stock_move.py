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
