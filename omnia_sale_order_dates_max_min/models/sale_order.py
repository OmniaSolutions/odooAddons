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
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
import datetime
from openerp import models
from openerp import api
from openerp import fields
from openerp import _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    @api.depends('order_line.customer_lead', 'order_line', 'date_order')
    def _get_oldest_commitment_date(self):
        """Compute the commitment date"""
        dates_list = []
        for order in self:
            dates_list = []
            order_datetime = datetime.datetime.strptime(order.date_order, DEFAULT_SERVER_DATETIME_FORMAT)
            for line in order.order_line:
                if line.state == 'cancel':
                    continue
                dt = order_datetime + datetime.timedelta(days=line.customer_lead or 0.0)
                dt_s = dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                dates_list.append(dt_s)
            if dates_list:
                order.commitment_date_last = max(dates_list)

    commitment_date_last = fields.Datetime(compute='_get_oldest_commitment_date', store=True, string=_('Oldest Commitment Date'),
                                           help="""Date by which the last product is sure to be delivered. This is
                                                    date that you can promise to the customer, based on the
                                                    Product Lead Times.""")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: