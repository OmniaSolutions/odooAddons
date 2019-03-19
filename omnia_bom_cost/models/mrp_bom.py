# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2010-2012 OpenERP s.a. (<http://openerp.com>).
#
#
#    Author : Smerghetto Daniel  (Omniasolutions)
#    mail:daniel.smerghetto@omniasolutions.eu
#    Copyright (c) 2014 Omniasolutions (http://www.omniasolutions.eu)
#    Copyright (c) 2018 Omniasolutions (http://www.omniasolutions.eu)
#    All Right Reserved
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

'''
Created on Apr 17, 2018

@author: Matteo Boscolo
'''
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
import logging
import datetime
from datetime import timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class MrpBom(models.Model):
    _name = "mrp.bom"
    _inherit = ['mrp.bom']

    @api.multi
    def _compute_bom_cost(self):
        for bom in self:
            totale_cost = 0.0
            for bom_line in bom.bom_line_ids:
                if bom_line.related_bom_ids:
                    for sub_bom in bom_line.related_bom_ids:
                        if bom.type in [sub_bom.type, 'phantom']:
                            if sub_bom:
                                totale_cost = totale_cost + sub_bom.standard_price * bom_line.product_qty
                                break
                else:
                    totale_cost = totale_cost + bom_line.product_id.standard_price * bom_line.product_qty
            bom.standard_price = totale_cost
    standard_price = fields.Float(compute=_compute_bom_cost)



