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


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    commitment_date_last = fields.Datetime(
        compute='_get_oldest_commitment_date', store=True,
        string=_('Oldest Commitment Date'),
        help="""
        Date by which the last product is sure to be delivered. This is 
        date that you can promise to the customer, based on the Product Lead Times.
        """
    )

    @api.depends('order_line.customer_lead', 'order_line', 'date_order')
    def _get_oldest_commitment_date(self):
        """Compute the commitment date"""
        for order in self:
            dates = []
            if not order.date_order:
                continue
            for line in order.order_line:
                if line.state == 'cancel':
                    continue
                dt = order.date_order + timedelta(days=line.customer_lead or 0.0)
                dates.append(dt)
            order.commitment_date_last = max(dates) if dates else False
