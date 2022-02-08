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
    def getPoLines(self, start_date, end_date, product_id=False):
        out = {}
        search_filter = [
            ('purchase_line_id', '!=', False),
            ('date', '>=', str(start_date)),
            ('date', '<=', str(end_date))
            ]
        if product_id:
            search_filter.append(('product_id', '=', product_id.id))
        moves = self.env['stock.move'].search(search_filter)
        
        average_dict = {}
        for move in moves:
            average_dict.setdefault(move.product_id, {})
            average_dict[move.product_id].setdefault(move.purchase_line_id.price_unit, 0)
            average_dict[move.product_id][move.purchase_line_id.price_unit] += move.product_uom_qty
        
        for move in moves:
            out.setdefault(move.product_id, {'qty': 0, 'price': 0})
            out[move.product_id]['qty'] += move.product_uom_qty
            
            if not out[move.product_id]['price']: # weighted average for price
                up = 0
                down = 0
                for price_unit, qty in average_dict.get(move.product_id, {}).items():
                    up += price_unit * qty
                    down += qty
                if up and down:
                    out[move.product_id]['price'] = up / down
        return out

    @api.model
    def getOutLocations(self):
        stockLocation = self.env['stock.location']
        availableLoctypes = ['production', 'inventory', 'customer'] # check internal
        return stockLocation.search([('usage', 'in', availableLoctypes)])

    @api.model
    def getStockMovesOut(self, start_date, end_date, warehouse_id=False, location_id=False, product_id=False):
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
        search_filter = [
            ('state', '=', 'done'),
            ('location_dest_id', 'in', locations.ids),
            ('date', '>=', str(start_date)),
            ('date', '<=', str(end_date)),
            ]
        if product_id:
            search_filter.append(('product_id', '=', product_id.id))
        stockMoves = stockMoveEnv.search(search_filter)
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
        if current_stock > 0:
            if lifos:
                lifos.write(vals)
            else:
                lifos.create(vals)
        else:
            if lifos and not lifos.imported:
                lifos.write(vals)

    @api.multi
    def action_generate_lifo(self):
        logging.info('[action_generate_lifo] start')
        for wizard in self:
            category_ids = wizard.product_category_ids
            product_id = wizard.product_id
            warehouse_id = wizard.warehouse_id
            location_id = wizard.location_id
            start_date, end_date, year = self.getTargetDates(wizard.year)
            product_ids = self.getAvailableProducts(category_ids, product_id)
            product_ids_len = len(product_ids.ids)
            logging.info('LIFO products to evaluate %r' % (product_ids_len))
            po_lines_dict = self.getPoLines(start_date, end_date, product_id)
            stock_moves_out = self.getStockMovesOut(start_date, end_date, warehouse_id, location_id, product_id)
            lenToeval = len(product_ids.ids)
            for index, product_id in enumerate(product_ids):
                if index % 300 == 0:
                    logging.info('[action_generate_lifo] %s / %s' % (index, lenToeval))
                average = po_lines_dict.get(product_id, {}).get('price', 0)
                qty_in = po_lines_dict.get(product_id, {'qty': 0.0}).get('qty', 0.0)
                current_stock = 0 # All time stock qty available
                for quant in product_id.stock_quant_ids:
                    if quant.in_date <= str(end_date) and quant.location_id.usage == 'internal':
                        if location_id and quant.location_id == location_id:
                            current_stock += quant.qty
                        elif warehouse_id and quant.location_id.get_warehouse() == warehouse_id:
                            current_stock += quant.qty
                        elif not warehouse_id and not location_id:
                            current_stock += quant.qty
                qty_out = stock_moves_out.get(product_id, {'qty': 0.0}).get('qty', 0.0)
                self.checkCreateStockLifo(product_id, qty_in, qty_out, average, year, current_stock)
                self.recomputeLifoQty(product_id, current_stock, year)
        logging.info('[action_generate_lifo] end')
    
    @api.model
    def recomputeLifoQty(self, product_id, current_stock, year):
        stockLifoEnv = self.env['stock.lifo']
        stock_lifos = stockLifoEnv.search([
            ('product_id', '=', product_id.id),
            ], order='year asc')
        stock_qty = 0
        for index, stock_lifo in enumerate(stock_lifos):
            remaining_qty = stock_lifo.remaining_year_qty
            if index == 0:
                stock_lifo.computed_qty = remaining_qty
            elif remaining_qty > stock_qty:
                qty_to_add = remaining_qty - stock_qty
                stock_lifo.computed_qty = qty_to_add
            elif remaining_qty <= stock_qty:
                stock_lifo.computed_qty = 0
                stock_lifo.avg_price = 0
            stock_lifo.total_amount = stock_lifo.computed_qty * stock_lifo.avg_price
            stock_qty = remaining_qty
        
        
        # for stock_lifo in stock_lifos:
            # if stock_lifo.year == str(year):
                # last_year = stock_lifo
                # continue
            # if stock_lifo == stock_lifos[-1]:
                # stock_lifo.computed_qty = current_stock
                # break
            # if last_year and current_stock > stock_lifo.remaining_year_qty:
                # last_year.computed_qty = current_stock - stock_lifo.remaining_year_qty
                # last_year.total_amount = last_year.computed_qty * last_year.avg_price
                # current_stock = stock_lifo.remaining_year_qty
            # if not last_year.avg_price and stock_lifo and last_year:
                # last_year.avg_price = stock_lifo.avg_price
            # last_year = stock_lifo
            # if current_stock <= 0:
                # break
                
        
