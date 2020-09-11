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
import shutil
import stat

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
from openpyxl import load_workbook
from odoo import _
import tempfile
import os
import base64


class InventoryValuation(models.TransientModel):
    _name = "inventory.valuation"

# descrizione in italiano
# Security

    ref_date = fields.Date(_('Date reference'))
    warehouse_id = fields.Many2one('stock.warehouse', _('Warehouse'))
    location_id = fields.Many2one('stock.location', _('Location'))
    show_zero = fields.Boolean(_('View zero quantity'))
    datas_fname = fields.Char(_('Optional Filename'))
    datas = fields.Binary(_('File content'))

    def filterLocationsByWarehouse(self, target_stock, locations):
        out = self.env['stock.location']
        
        def checkRecursion(target, location):
            if location.id == target.id:
                return True
            if not location.location_id:
                return False
            return checkRecursion(target, location.location_id)
            
            
        for location in locations:
            if location.id == target_stock.id:
                out += location
                continue
            if checkRecursion(target_stock, location):
                out += location
        return out

    @api.multi
    def action_generate_inventory(self):
        location_ids = self.env['stock.location']
        if self.location_id:
            location_ids = self.location_id
        else:
            internal_locations = location_ids.search([('usage', '=', 'internal')])
            if not self.warehouse_id:
                location_ids = internal_locations
            else:
                location_ids = self.filterLocationsByWarehouse(self.warehouse_id.lot_stock_id, internal_locations)
        params = {
            'ref_date': self.ref_date or '5000-01-01',
            'location_ids': tuple(location_ids.ids),
            }
        zero_condition = 'price_unit_on_quant != 0 and '
        if self.show_zero:
            zero_condition = ''
        sql_query = """select avg(price_unit_on_quant),
                              sum(price),
                              ss.product_id,
                              ss.product_categ_id,
                              ss.location_id,
                              sum(quantity) from (
                                    select price_unit_on_quant, 
                                           quantity * price_unit_on_quant as price,
                                           product_id,
                                           product_categ_id,
                                           quantity,
                                           location_id
                                           from stock_history where """
        sql_query += zero_condition
        sql_query += """
                                               date < %(ref_date)s and 
                                               location_id in %(location_ids)s 
                                               order by product_id) as ss
                                    group by ss.location_id, ss.product_categ_id, ss.product_id order by ss.location_id asc, ss.product_categ_id asc, ss.product_id asc"""
        self.env.cr.execute(sql_query, params)
        results = self.env.cr.fetchall()
        if not results:
            return
        template_file = os.path.join(os.path.dirname(__file__), 'inventory_valuation.xlsx')
        out_fname = self.datas_fname
        if not out_fname:
            out_fname = 'stock_inventory'
        if not out_fname.endswith('.xlsx'):
            out_fname += '.xlsx'
        self.datas_fname = out_fname
        full_path = os.path.join(tempfile.gettempdir(), out_fname)
        shutil.copy(template_file, full_path)
        os.chmod(full_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        workbook = load_workbook(filename=full_path)
        worksheetpivot = workbook.get_sheet_by_name('inventory')
        worksheetpivot.cell(row=1, column=2).value = self.warehouse_id.name if  self.warehouse_id else ''
        worksheetpivot.cell(row=2, column=2).value = self.ref_date or ''
        worksheetpivot.cell(row=3, column=2).value = self.location_id.name if self.location_id else ''

        worksheet = workbook.get_sheet_by_name('data_sheet')
        row_counter = 2
        prec = self.env['decimal.precision'].precision_get('Product Price')
        location_cache = {}
        category_cache = {}
        for price_unit, price_total, product_id, product_categ_id, location_id, quantity in results:
            if price_total == 0 and not self.show_zero:
                continue
            product_product = self.env['product.product'].browse(product_id)
            if product_product.type != 'product':
                continue
            location_name =  location_cache.get(location_id)
            if not location_name:
                location_name = self.env['stock.location'].browse(location_id).complete_name
                location_cache[location_id]=location_name
            categ  = category_cache.get(product_categ_id)
            if not categ:
                categ = self.env['product.category'].browse(product_categ_id).display_name
                category_cache[product_categ_id] = categ
            prod_name = product_product.display_name
            worksheet.cell(row=row_counter, column=1).value = location_name
            worksheet.cell(row=row_counter, column=2).value = categ
            worksheet.cell(row=row_counter, column=3).value = prod_name
            worksheet.cell(row=row_counter, column=4).value = round(price_unit, prec)
            worksheet.cell(row=row_counter, column=5).value = round(price_total, prec)
            worksheet.cell(row=row_counter, column=6).value = round(quantity, prec)
            row_counter += 1
        workbook.save(full_path)
        os.chmod(full_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        with open(full_path, 'rb') as f:
            fileContent = f.read()
            if fileContent:
                self.datas = base64.encodestring(fileContent)
        return {'name': _('Inventory Valuation'),
                'view_type': 'form',
                "view_mode": 'form',
                'res_model': 'inventory.valuation',
                'target': 'new',
                'res_id': self.ids[0],
                'type': 'ir.actions.act_window',
                'domain': "[]"}


