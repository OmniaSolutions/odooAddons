##############################################################################
#
#    OmniaSolutions, Your own solutions
#    Copyright (C) 2020 OmniaSolutions (<https://omniasolutions.website>). All Rights Reserved
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
# Leonardo Cazziolati
# leonardo.cazziolati@omniasolutions.eu
# 04-12-2020

from odoo import models, fields, api, _
import json


class StockLifo(models.Model):

    _name = 'stock.lifo'
    _description = "Lifo configuration"
    
    product_id = fields.Many2one("product.product", _("Product"))
    qty_in = fields.Float(string=_('Quantity In'))
    qty_out = fields.Float(string=_('Quantity Out'))
    avg_price = fields.Float(string=_('Average Product Price'))
    total_amount = fields.Float(_('Amount Total'))
    year = fields.Char(string=_("Year"))
    remaining_year_qty = fields.Float(_('Remaining Year Qty'))
    computed_qty = fields.Float(_('Computed Qty'))
    lifo_desc = fields.Char(_('Old Desc'))
    imported = fields.Boolean(_('Imported'))

    def findProduct(self, code):
        product_env = self.env['product.product']
        product_tmpl_env = self.env['product.template']
        products = product_env.search([
            ('engineering_code', '=', code)
            ], order='engineering_revision desc', limit=1)
        if not products:
            products = product_env.search([
                ('name', '=', code)
                ], order='engineering_revision desc', limit=1)
            if not products:
                products = product_env.search([
                    ('default_code', 'like', code)
                    ], order='engineering_revision desc', limit=1)
                if not products:
                    templates = product_tmpl_env.search([
                        ('default_code', 'like', code)
                        ], order='engineering_revision desc', limit=1)
                    if templates:
                        products = templates.product_variant_ids
                        if not products:
                            templates = product_tmpl_env.search([
                                ('name', 'like', code)
                                ], order='engineering_revision desc', limit=1)
                            if templates:
                                products = templates.product_variant_ids
        for product in products:
            return product
        return None

    @api.model
    def importLifoFromExcel(self, line):
        line = json.loads(line)
        product_name = line['articolo']
        desc = line['descrizione']
        rim_finale = line['rim_finale']
        anno = line['anno']
        costo_medio = line['costo_medio']
        importo = line['importo']
        rim_calcolata = line['rim_calcolata']
        product_id = self.findProduct(product_name)
        if not product_id:
            return json.dumps([False, 'Cannot find product %r' % (product_name)])
        vals = {
            'product_id': product_id.id,
            'avg_price': costo_medio,
            'total_amount': importo,
            'year': str(anno),
            'remaining_year_qty': rim_finale,
            'computed_qty': rim_calcolata,
            'lifo_desc': desc,
            'imported': True,
            }
        lifo_lines = self.search([('product_id', '=', product_id.id),
                                  ('year', '=', str(anno))
                                  ])
        if lifo_lines:
            res = lifo_lines.write(vals)
        else:
            lifo_lines.create(vals)
            res = True
        return json.dumps([res, ''])
