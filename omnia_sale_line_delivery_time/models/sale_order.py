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
from datetime import timedelta
from odoo import _, api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_delivery_date = fields.Datetime(
        string='Delivery Date',
        compute='_compute_product_delivery_date',
    )

    @api.depends('customer_lead', 'order_id.date_order', 'product_id')
    def _compute_product_delivery_date(self):
        for line in self:
            if line.product_id and line.order_id.date_order:
                line.product_delivery_date = line.order_id.date_order + timedelta(
                    days=line.customer_lead or 0
                )
            else:
                line.product_delivery_date = False

    @api.onchange('customer_lead')
    def _onchange_customer_lead(self):
        self._compute_product_delivery_date()
