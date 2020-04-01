# -*- coding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, ERP-PLM-CAD Open Source Solutions
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
import logging
import datetime
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
from odoo.exceptions import UserError
from datetime import timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class StockMove(models.Model):
    _inherit = ['stock.move']
    
    omnia_procurement_ids = fields.One2many('procurement.order',
                                           'omnia_move_id',
                                           string='OR.Proc')
    @api.multi
    def getOmniaProcurementQty(self):
        out = 0.0
        for procurement_id in self.omnia_procurement_ids:
            out =+ procurement_id.product_qty
        return out

class ProcurementOrder(models.Model):
    _inherit = ['procurement.order']
    
    omnia_move_id = fields.Many2one('stock.move',
                                           string='Omnia releted move')
    