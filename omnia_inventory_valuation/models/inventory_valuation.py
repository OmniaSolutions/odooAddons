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
import csv
import tempfile
import os
import base64


class InventoryValuation(models.TransientModel):
    _name = "inventory.valuation"

    ref_date = fields.Date('Date reference')
    location_id = fields.Many2one('stock.location', 'Location')
    datas_fname = fields.Char('Out Filename')
    datas = fields.Binary('File content')
    price_unit_grater = fields.Float('Price unit grater than', default=0)
    
    @api.multi
    def action_generate_inventory(self):
        params = {
            'ref_date': self.ref_date or '5000-01-01',
            'location_id': self.location_id.id,
            'price_unit_grater': self.price_unit_grater,
            }
        sql_query = """select sum(price_unit_on_quant), sum(price) , ss.product_id, ss.product_categ_id from (
                            select price_unit_on_quant, quantity * price_unit_on_quant as price, product_id, product_categ_id, "date" from stock_history where price_unit_on_quant > %(price_unit_grater)s  and date < %(ref_date)s and location_id = %(location_id)s order by product_id) as ss group by ss.product_id, ss.product_categ_id order by ss.product_categ_id desc"""
        self.env.cr.execute(sql_query, params)
        results = self.env.cr.fetchall()
        if not results:
            return
        out_fname = self.datas_fname
        if not out_fname:
            out_fname = 'stock_inventory'
        if not out_fname.endswith('.csv'):
            out_fname += '.csv'
        self.datas_fname = out_fname
        full_path = os.path.join(tempfile.gettempdir(), out_fname)
        with open(full_path, 'w') as file_obj:
            writer = csv.writer(file_obj)
            writer.writerow(['Product', 'Category', 'Price unit', 'Price total'])
            for price_unit, price_total, product_id, product_categ_id in results:
                prod_name = self.env['product.product'].browse(product_id).display_name
                categ = self.env['product.category'].browse(product_categ_id).display_name
                writer.writerow([str(prod_name.encode('utf-8')), categ, price_unit, price_total])
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


