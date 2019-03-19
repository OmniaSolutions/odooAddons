# -*- encoding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, Open Source Management Solution
#    Copyright (C) 2010-2018 OmniaSolutions (<http://www.omniasolutions.eu>). All Rights Reserved
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

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
'''
Created on Nov 1, 2018

@author: mboscolo
'''

from odoo import models
from odoo import fields
from odoo import api
from odoo import _
import logging
import datetime


class StockMoveLine(models.Model):

    _inherit = ['stock.move.line']

    @api.model
    def getAllQuantAtDate(self, date_to):
        out = {}
        query = """select sum(qty_done) qty , product_id, location_id, location_dest_id  from stock_move_line  where date <= %r and state='done' group by product_id, location_id,location_dest_id
                """ % (date_to)
        self.env.cr.execute(query)
        for row in self._cr.fetchall():
            quant_qty = row[0] * 1.0
            product_id = row[1]
            location_id = row[2]
            location_dest_id = row[3]
            key_negative = "%d_%d" % (location_id, product_id)
            if key_negative in out:
                out[key_negative] = out[key_negative] - quant_qty
            else:
                out[key_negative] = quant_qty * -1.0
            key_positive = "%d_%d" % (location_dest_id, product_id)
            if key_positive in out:
                out[key_positive] = out[key_positive] + quant_qty
            else:
                out[key_positive] = quant_qty
        return out
