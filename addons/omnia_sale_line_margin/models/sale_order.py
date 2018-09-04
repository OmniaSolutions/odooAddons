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
Created on Jul 21, 2017

@author: daniel
'''
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import models
from odoo import api
from odoo import fields
from odoo import _


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('price_unit', 'discount')
    def _compute_line_margin(self):
        for lineBrws in self:
            margin = (lineBrws.price_unit / 100) * (100 - lineBrws.discount)
            lineBrws.sale_order_line_margin = margin - lineBrws.purchase_price

    sale_order_line_margin = fields.Float(_('Margin'), compute="_compute_line_margin")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: