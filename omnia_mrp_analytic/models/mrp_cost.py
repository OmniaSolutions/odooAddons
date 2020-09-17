# -*- encoding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, Your own solutions
#    Copyright (C) 2019 OmniaSolutions (<http://omniasolutions.eu>). All Rights Reserved
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
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
from odoo.exceptions import UserError


class ImportWizard(models.TransientModel):
    _name = 'import.wizard'
    
    product = fields.Many2one('product.product', string=_('Product'))
    
    @api.model
    def calculateAnalyticCost(self,
                              product_id,
                              project_id):
        if not product_id:
            raise UserError(_('[ERROR] Missing product'))
        
        evaluated = {}

        def _calculateAnalyticCost(product_id,
                                   project_id,
                                   production_id=False):
            tot_price = 0
            if not production_id:
                production_id = self.env['mrp.production'].search([('product_id', '=', product_id), ('project_id', '=', project_id), ('state', '=', 'done')])
            for production in production_id:
                for raw in production.move_raw_ids:
                    if raw.product_id not in evaluated:
                        evaluated[raw.product_id] = []
                    children_productions = self.env['mrp.production'].search([('product_id', '=', raw.product_id.id), ('project_id', '=', project_id), ('state', '=', 'done')])
                    if not evaluated[raw.product_id]:
                        evaluated[raw.product_id] = children_productions.ids
                    if children_productions:
                        production_child_id = evaluated[raw.product_id].pop(0)
                        children_amount = _calculateAnalyticCost(raw.product_id.id, project_id, self.env['mrp.production'].browse(production_child_id))
                        tot_price += children_amount
                    else:
                        unit_price = self.getUnitPrice(raw.product_id.id, raw.price_unit, production.write_date) * raw.product_uom_qty
                        tot_price += unit_price
            return tot_price

        return _calculateAnalyticCost(product_id, project_id)
        
    def getUnitPrice(self, raw_product, price_unit, write_date):
        stock_historys = self.env['stock.history'].search([('product_id', '=', raw_product),
                                                              ('date', '<=', write_date),
                                                              ('quantity', '>', 0)], order="date desc")
        for stock_history in stock_historys:
            if stock_history.price_unit_on_quant != 0:
                return stock_history.price_unit_on_quant
            break
        invoice_lines = self.env['account.invoice.line'].search([('product_id', '=', raw_product),
                                                                      ('write_date', '<=', write_date)], order="write_date desc")
        for invoice_line in invoice_lines:
            if invoice_line.price_unit != 0:
                return invoice_line.price_unit
            break
        purchase_lines = self.env['purchase.order.line'].search([('product_id', '=', raw_product),
                                                                      ('write_date', '<=', write_date)], order="write_date desc")
        for purchase_line in purchase_lines:
            if purchase_line.price_unit != 0:
                return purchase_line.price_unit
            break
        return price_unit
    
    @api.model
    def createCostOnAnalyticAccount(self,
                                    product_id,
                                    cost,
                                    active_id):
        product_name = self.env['product.product'].browse(product_id).display_name
        line_to_create = {'name': _('Automatic calculation of production cost [%s]') % (product_name),
                          'account_id': active_id,
                          'amount': cost,
                          'product_id': product_id}
        check_line_id = self.env['account.analytic.line'].search([('product_id', '=', product_id), ('account_id', '=', active_id)])
        if check_line_id:
            for line_id in check_line_id:
                line_id.write({'amount': cost})
        else:
            self.env['account.analytic.line'].create(line_to_create)
    
    @api.multi
    def import_data(self):
        product_id = self.product.id
        active_id = self.env.context.get('active_id', False)
        project_id = self.env['project.project'].search([('analytic_account_id', '=', active_id)])
        cost = self.calculateAnalyticCost(product_id,
                                          project_id.id)
        self.createCostOnAnalyticAccount(product_id,
                                         cost,
                                         active_id)
        vals = self.env.ref('analytic.account_analytic_line_action').read()[0]
        vals['domain'] = vals.get('domain', '').replace('active_id', str(active_id))
        vals['context'] = vals.get('context', '').replace('active_id', str(active_id))
        return vals
