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
import logging
import datetime


class StockLifoWizard(models.TransientModel):

    _name = 'stock.lifo.wizard'
    _description = "Lifo wizard"

    product_category_ids = fields.Many2many(comodel_name='product.category', string=_("Categories"))
    product_id = fields.Many2one("product.product", _("Product"))
    year = fields.Char(_('Year'), default=datetime.datetime.now().year)
    warehouse_id = fields.Many2one('stock.warehouse', _('Warehouse'))
    location_id = fields.Many2one('stock.location', _('Location'))

    @api.model
    def getAvailableProducts(self, category_ids, product_id):
        product_ids = self.env['product.product']
        if category_ids and not product_id:
            product_ids = product_ids.search([
                ('categ_id', 'in', category_ids.ids),
                ('type', '=', 'product')
                ])
        elif product_id:
            product_ids = product_id
        else:
            product_ids = self.env['product.product'].search([
                ('type', '=', 'product')
                ])
        return product_ids

    @api.model
    def getPoLines(self, start_date, end_date):
        out = {}
        poenv = self.env['purchase.order']
        pos = poenv.search([
            ('state', '=', 'purchase'),
            ('date_order', '>=', str(start_date)),
            ('date_order', '<=', str(end_date))
            ])
        for po in pos:
            for pol in po.order_line:
                product = pol.product_id
                if product.type == 'product':
                    if product not in out:
                        out[product] = {'prices': [], 'qty': 0.0}
                    out[product]['prices'].append(pol.price_unit)
                    moves = self.env['stock.move'].search([
                        ('purchase_line_id', '=', pol.id)
                        ])
                    for move in moves:
                        out[product]['qty'] += move.product_uom_qty
        return out

    @api.model
    def getOutLocations(self):
        stockLocation = self.env['stock.location']
        availableLoctypes = ['production', 'inventory'] # check internal
        return stockLocation.search([('usage', 'in', availableLoctypes)])

    @api.model
    def getStockMovesOut(self, start_date, end_date, warehouse_id=False, location_id=False):
        out = {}
        stockMoveEnv = self.env['stock.move']
        locations = self.env['stock.location']
        if location_id:
            locations = location_id
        elif warehouse_id:
            location_ids = self.getOutLocations()
            for location in location_ids:
                if location.get_warehouse() == warehouse_id:
                    locations += location
        else:
            locations = self.getOutLocations()
        stockMoves = stockMoveEnv.search([
            ('state', '=', 'done'),
            ('location_id', 'in', location_id.ids),
            ('date', '>=', str(start_date)),
            ('date', '<=', str(end_date)),
            ])
        for stockMove in stockMoves:
            product = stockMove.product_id
            if product.type == 'product':
                if product not in out:
                    out[product] = {'qty': 0.0}
                out[product]['qty'] += stockMove.product_qty
        return out

    @api.model
    def getTargetDates(self, year):
        year = int(year)
        start_year = datetime.datetime(year, 1, 1)
        end_year = datetime.datetime(year, 12, 31)
        return start_year, end_year, year

    def checkCreateStockLifo(self, product_id, qty_in, qty_out, average, year, current_stock):
        stockLifoEnv = self.env['stock.lifo']
        lifos = stockLifoEnv.search([
            ('product_id', '=', product_id.id),
            ('year', '=', year)
            ])
        if current_stock < 0:
            current_stock = 0
        total_amount = 0
        computed_qty = 0
        vals = {
            'product_id': product_id.id,
            'qty_in': qty_in,
            'qty_out': qty_out,
            'avg_price': average,
            'total_amount': total_amount,
            'year': year,
            'remaining_year_qty': current_stock,
            'computed_qty': computed_qty,
            }
        if lifos:
            lifos.write(vals)
        else:
            lifos.create(vals)

    @api.multi
    def action_generate_lifo(self):
        for wizard in self:
            category_ids = wizard.product_category_ids
            product_id = wizard.product_id
            warehouse_id = wizard.warehouse_id
            location_id = wizard.location_id
            start_date, end_date, year = self.getTargetDates(wizard.year)
            product_ids = self.getAvailableProducts(category_ids, product_id)
            product_ids_len = len(product_ids.ids)
            logging.info('LIFO products to evaluate %r' % (product_ids_len))
            po_lines_dict = self.getPoLines(start_date, end_date)
            stock_moves_out = self.getStockMovesOut(start_date, end_date, warehouse_id, location_id)
            for product_id in product_ids:
                prices = po_lines_dict.get(product_id, {'prices': []}).get('prices', [])
                qty_in = po_lines_dict.get(product_id, {'qty': 0.0}).get('qty', 0.0)
                if not prices:
                    average = 0
                else:
                    average = sum(prices) / float(len(prices))
                current_stock = 0
                for quant in product_id.stock_quant_ids:
                    if location_id and quant.location_id == location_id:
                        current_stock += quant.qty
                    elif warehouse_id and quant.location_id.get_warehouse() == warehouse_id:
                        current_stock += quant.qty
                    elif not warehouse_id and not location_id:
                        current_stock = product_id.qty_available
                qty_out = stock_moves_out.get(product_id, {'qty': 0.0}).get('qty', 0.0)
                self.checkCreateStockLifo(product_id, qty_in, qty_out, average, year, current_stock)
                self.recomputeLifoQty(product_id, current_stock, year)
    
    @api.model
    def recomputeLifoQty(self, product_id, current_stock, year):
        stockLifoEnv = self.env['stock.lifo']
        stock_lifos = stockLifoEnv.search([
            ('product_id', '=', product_id.id),
            ], order='year desc')
        last_year = self.env['stock.lifo']
        for stock_lifo in stock_lifos:
            if stock_lifo.year == str(year):
                last_year = stock_lifo
                continue
            if stock_lifo == stock_lifos[-1]:
                stock_lifo.computed_qty = current_stock
                break
            if current_stock > stock_lifo.remaining_year_qty:
                last_year.computed_qty = current_stock - stock_lifo.remaining_year_qty
                last_year.total_amount = last_year.computed_qty * last_year.avg_price
                current_stock = stock_lifo.remaining_year_qty
            last_year = stock_lifo
            if current_stock <= 0:
                break
                
        
