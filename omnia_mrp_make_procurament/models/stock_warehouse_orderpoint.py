# -*- coding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, ERP-PLM-CAD Open Source Solution
#    Copyright (C) 2011-2020 https://OmniaSolutions.website
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this prograIf not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
'''
Created on 3 Mar 2020

@author: mboscolo
'''

from collections import namedtuple
from datetime import datetime
from dateutil import relativedelta

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

import logging

_logger = logging.getLogger(__name__)


class Orderpoint(models.Model):
    """ Defines Minimum stock rules. """
    _inherit = "stock.warehouse.orderpoint"
    _description = "Minimum Inventory Rule"
 
    def subtract_procurements_from_orderpoints1(self, move_ids):
        '''This function returns quantity of product that needs to be deducted from the orderpoint computed quantity because there's already a procurement created with aim to fulfill it.
        '''
        self._cr.execute("""SELECT orderpoint.id, procurement.id, procurement.product_uom, procurement.product_qty, template.uom_id, move.product_qty
            FROM stock_warehouse_orderpoint orderpoint
            JOIN procurement_order AS procurement ON procurement.orderpoint_id = orderpoint.id
            JOIN product_product AS product ON product.id = procurement.product_id
            JOIN product_template AS template ON template.id = product.product_tmpl_id
            LEFT JOIN stock_move AS move ON move.procurement_id = procurement.id
            WHERE procurement.state not in ('done', 'cancel')
                AND (move.state IS NULL OR move.state != 'draft')
                AND orderpoint.id IN %s
                AND move.id IN %s
            ORDER BY orderpoint.id, procurement.id
        """, (tuple(self.ids),tuple(move_ids),))
        UoM = self.env["product.uom"]
        procurements_done = set()
        res = dict.fromkeys(self.ids, None)
        for orderpoint_id, procurement_id, product_uom_id, procurement_qty, template_uom_id, move_qty in self._cr.fetchall():
            if procurement_id not in procurements_done:  # count procurement once, if multiple move in this orderpoint/procurement combo
                procurements_done.add(procurement_id)
                res[orderpoint_id] += UoM.browse(product_uom_id)._compute_quantity(procurement_qty, UoM.browse(template_uom_id), round=False)
            if move_qty:
                res[orderpoint_id] -= move_qty
        return res