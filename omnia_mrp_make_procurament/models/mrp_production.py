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
#    Copyright (c) 2014 Omniasolutions (https://www.omniasolutions.website)
#    Copyright (c) 2018 Omniasolutions (https://www.omniasolutions.website)
#    Copyright (c) 2021 Omniasolutions (https://www.omniasolutions.website
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


class StockMove(models.Model):
    _inherit = "stock.move"
    run_a_executed = fields.Boolean("RunA Executed")    
    
    
class MrpProduction(models.Model):
    _inherit = ['mrp.production']

    # def create_procuraments(self):
    #     production_to_call = []
    #     stock_warehouse_orderpoint = self.env['stock.warehouse.orderpoint']
    #     for mrp_production_id in self:
    #         ids=[]
    #         for line in mrp_production_id.move_raw_ids:
    #             if line.state not in ['done', 'cancel'] and line.product_qty - line.quantity_done > 0:
    #                 ids.append(line.product_id.id)
    #         ctx=self.env.context.copy()
    #         ctx['omnia_product_ids'] = ids
    #         try:
    #             if mrp_production_id.project_id:
    #                 ctx['omnia_analytic_id'] = mrp_production_id.project_id.analytic_account_id.id
    #         except Exception as ex:
    #             logging.warning(ex)
    #         date_now = datetime.datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    #         self.env['procurement.group'].with_context(ctx).run_scheduler(company_id=self.env.user.company_id.id)
    #         self.search([('create_date', '>', date_now)]).create_procuraments()
        
    def create_procuraments(self):
        product_replenish = self.env['product.replenish']
        for mrp_production_id in self:
            mrp_production_id.action_assign()
            mrp_context = self.env.context.copy()
            mrp_context['omnia_analytic_id'] = mrp_production_id.project_id.analytic_account_id.id
            for line in mrp_production_id.move_raw_ids:
                qty_to_order = line.product_uom_qty - line.reserved_availability + line.quantity_done
                if qty_to_order > 0 and not line.run_a_executed:
                    try:
                        replenish_wizard = product_replenish.with_context(mrp_context).create({'product_id': line.product_id.id,
                                                                     'product_tmpl_id': line.product_id.product_tmpl_id.id,
                                                                     'product_uom_id': line.product_id.uom_id.id,
                                                                     'quantity': qty_to_order,
                                                                     'warehouse_id': mrp_production_id.location_src_id.get_warehouse().id,
                                                                    })
                        replenish_wizard.custom_launch_replenishment('Run.A', mrp_production_id.name)
                        line.run_a_executed=True
                    except Exception as ex:
                        logging.error(ex)
        