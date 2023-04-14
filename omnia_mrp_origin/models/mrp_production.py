# -*- encoding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, Open Source Management Solution    
#    Copyright (C) 2010-2011 OmniaSolutions (<http://www.omniasolutions.eu>). All Rights Reserved
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

'''
Created on Jul 21, 2017

@author: daniel
'''
from odoo import models
from odoo import api
from odoo import _
import logging


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def recomputeOrigin(self, product_id, origin=''):
        product = self.env['product.product']
        product_id = product.browse(product_id)
        report_forecast = self.env['report.stock.report_product_product_replenishment']
        report_vals = report_forecast._get_report_data(False, [product_id.id])
        for line in report_vals.get('lines', []):
            replenishment_filled = line.get('replenishment_filled', False)
            sale_order = line.get('document_out', self.env['sale.order'])
            quantity = line.get('quantity', 0)
            if not replenishment_filled and quantity:
                origin += ' | %s[%s]' % (sale_order.display_name, quantity)
        return origin

    @api.model
    def create(self, vals):
        origin = vals.get('origin', '')
        from_orderpoint = self.env.context.get('from_orderpoint', False)
        if from_orderpoint:
            vals['origin'] = self.recomputeOrigin(vals['product_id'], origin)
        elif origin:
            productions = self.env['mrp.production'].search([('name', '=', origin)])
            for production in productions:
                prod_origin = production.origin or ''
                tokens = prod_origin.split(' | ')
                if len(tokens) > 0:
                    sale_info = tokens[-1]
                    sale_order = sale_info.split('[')[0]
                    logging.debug('Search sale order %r' % (sale_order))
                    sales = self.env['sale.order'].search([('name', '=', sale_order)])
                    for _sale_id in sales:
                        vals['origin'] = '%s | %s' % (vals['origin'], sale_order)
                        break
        return super(MrpProduction, self).create(vals)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: