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
from odoo import _, api, models, fields
import logging
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

    
class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    omnia_mrp_orig_move = fields.Many2one("stock.move",
                                          copy=False,
                                          string="Original Move")
    project_id = fields.Many2one('project.project', string="Project")
    omnia_analytic_id = fields.Many2one(related="project_id.auto_account_id", string="Conto Analitico")


    def getProcuramentGroup(self):
        for mrp_production_id in self:
            procurement_group_id = None
            for procurement_group_id in self.env['procurement.group'].search([('name','=', mrp_production_id.name)]):
                break
            if not procurement_group_id:
                procurement_group_id = self.env['procurement.group'].create({'name': mrp_production_id.name })
            return procurement_group_id

    @api.model
    def create_procurement_row(self,
                               product_id,
                               product_qty,
                               name,
                               order_point_id):

        date = fields.Datetime.now()

        warehouse = self.env['stock.warehouse'].search([
            ('lot_stock_id', '=', self.location_src_id.id)
        ], limit=1)

        """
        {
        'date_planned': '2023-11-18 17:16:15',
        'warehouse_id': stock.warehouse(1,),
        'orderpoint_id': stock.warehouse.orderpoint(8833,),
        'company_id': res.company(1,),
        'group_id': procurement.group()
        }
        """

        pg = self.env['procurement.group']

        proc = pg.Procurement(
            product_id,  # product
            product_qty,  # quantity
            product_id.uom_id,  # uom
            self.location_src_id,  # source location
            product_id.name,  # name
            name,  # origin
            self.env.user.company_id,  # company record
            {
                'date_planned': fields.Datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'company_id': self.env.user.company_id,
                'warehouse_id': self.env['stock.warehouse'].search([('lot_stock_id', '=', self.location_src_id.id)],
                                                                   limit=1),
                'orderpoint_id': order_point_id,
                'add_date_in_domain': True,
                'group_id': self.getProcuramentGroup(),
            }
        )
        self.env['procurement.group'].run([proc])

    def _generate_moves(self):
        mrp_context = self.env.context.copy()
        for mrp_production_id in self:
            analitic_id = mrp_production_id.project_id.analytic_account_id.id
            if analitic_id:
                mrp_context['omnia_analytic_id'] = analitic_id
                super(MrpProduction, mrp_production_id.with_context(mrp_context))._generate_moves()
            else:
                super(MrpProduction, mrp_production_id)._generate_moves()
        return True
