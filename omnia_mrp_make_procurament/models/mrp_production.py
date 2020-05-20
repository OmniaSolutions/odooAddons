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
Created on Dec 18, 2017

@author: daniel
'''
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
from odoo.exceptions import UserError
import logging
import datetime
from datetime import timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round


class MrpProduction(models.Model):
    _inherit = ['mrp.production']

    @api.multi
    def create_procuraments(self):
        production_to_call = []
        make_procurament = self.env['make.procurement']
        stock_warehouse_orderpoint = self.env['stock.warehouse.orderpoint']
        for mrp_production_id in self:
            ids=[]
            for line in mrp_production_id.bom_id.bom_line_ids:
                ids.append(line.product_id.id)
            ctx=self.env.context.copy()
            ctx['product_ids'] = ids
            date_now = datetime.datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            self.env['procurement.order'].with_context(ctx).run_scheduler(company_id=self.env.user.company_id.id)
            self.search([('create_date', '>', date_now)]).create_procuraments()
