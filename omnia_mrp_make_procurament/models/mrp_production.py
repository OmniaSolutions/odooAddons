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
    
    def getProcuramentGroup(self):
        for mrp_production_id in self:
            procurement_group_id = None
            for procurement_group_id in self.env['procurement.group'].search([('name','=',mrp_production_id.name)]):
                break
            if not procurement_group_id:
                procurement_group_id = self.env['procurement.group'].create({'name':mrp_production_id.name })
            return procurement_group_id
                
    @api.model
    def create_procurement_row(self,
                               product,
                               product_qty,
                               name,
                               order_point_id):
        date = datetime.datetime.now()
             
        vals = {
            'date_planned': date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'company_id': self.env.user.company_id,
            'warehouse_id': self.location_src_id.get_warehouse(),
            'orderpoint_id' : order_point_id,
            'add_date_in_domain': True,
            'group_id': self.getProcuramentGroup()
        }
        """
        {
        'date_planned': '2023-11-18 17:16:15',
        'warehouse_id': stock.warehouse(1,),
        'orderpoint_id': stock.warehouse.orderpoint(8833,),
        'company_id': res.company(1,),
        'group_id': procurement.group()
        }
        """
        self.env['procurement.group'].run(product,
                                          product_qty,
                                          product.uom_id,
                                          self.location_src_id,
                                          product.name,
                                          name,
                                          vals)
# product_context = dict(self._context, location=location_orderpoints[0].location_id.id)
# product_quantity = location_data['products'].with_context(product_context)._product_available()
# op_product_virtual = product_quantity[orderpoint.product_id.id]['virtual_available']
    
    def create_procuraments(self):
        sub_production_to_compute = self.env['product.product']
        for mrp_production_id in self:
            mrp_production_id.action_assign()
            mrp_context = self.env.context.copy()
            mrp_context['omnia_analytic_id'] = mrp_production_id.project_id.analytic_account_id.id
            for line in mrp_production_id.move_raw_ids: # line.product_id.get_theoretical_quantity(line.product_id.id, self.location_src_id.id, False, False, False, False)
                product_context = dict(self._context, location=self.location_src_id.id)
                product_quantity = line.product_id.with_context(product_context)._product_available()
                op_product_virtual = product_quantity[line.product_id.id]['virtual_available']
                
                for order_point_id in line.product_id.orderpoint_ids:
                    if self.location_src_id==order_point_id.location_id:
                        qty_in_progress = order_point_id._quantity_in_progress()
                        qty_to_order = -1.0 * (op_product_virtual+qty_in_progress[line.product_id.orderpoint_ids.id])
                        mrp_line_qty_to_order = line.product_uom_qty - line.reserved_availability + line.quantity_done
                        if mrp_line_qty_to_order<=mrp_line_qty_to_order:
                            qty_to_order=mrp_line_qty_to_order
                        if qty_to_order>0:
                            try:
                                self.with_context(mrp_context).create_procurement_row(line.product_id,
                                                                                      qty_to_order,
                                                                                      mrp_production_id.name,
                                                                                      order_point_id)
                                if line.product_id.route_ids.mapped("name")=='Produci':
                                    sub_production_to_compute+=line.product_id
                                line.run_a_executed=True
                                break
                            except Exception as ex:
                                logging.error(ex)
        for product_id in sub_production_to_compute:
            for mrp_production_id in self.search([('product_id','=', product_id.id)],
                                                   [('id','>', max(self.ids))]):      
                mrp_production_id.create_procuraments()
        