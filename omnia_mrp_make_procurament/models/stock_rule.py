# -*- coding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, ERP-PLM-CAD Open Source Solutions
#    Copyright (C) 2011-2021 https://OmniaSolutions.website
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
#    along with this prograIf not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
'''
Created on 26 Oct 2021

@author: mboscolo
'''
import logging
import datetime
from dateutil.relativedelta import relativedelta
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
from odoo.exceptions import UserError
from datetime import timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class StockRule(models.Model):
    _inherit = 'stock.rule'

    @api.multi
    def _run_buy(self, product_id, product_qty, product_uom, location_id, name, origin, values):
        cache = {}
        suppliers = product_id.seller_ids\
            .filtered(lambda r: (not r.company_id or r.company_id == values['company_id']) and (not r.product_id or r.product_id == product_id) and r.name.active)
        if not suppliers:
            msg = _('There is no vendor associated to the product %s. Please define a vendor for this product.') % (product_id.display_name,)
            raise UserError(msg)   
        supplier = self._make_po_select_supplier(values, suppliers)
        partner = supplier.name
        # we put `supplier_info` in values for extensibility purposes
        values['supplier'] = supplier

        domain = self._make_po_get_domain(values, partner)
        if domain in cache:
            po = cache[domain]
        else:
            po = self.env['purchase.order'].sudo().search([dom for dom in domain])
            po = po[0] if po else False
            cache[domain] = po
        if not po:
            vals = self._prepare_purchase_order(product_id, product_qty, product_uom, origin, values, partner)
            company_id = values.get('company_id') and values['company_id'].id or self.env.user.company_id.id
            po = self.env['purchase.order'].with_context(force_company=company_id).sudo().create(vals)
            cache[domain] = po
        elif not po.origin or origin not in po.origin.split(', '):
            if po.origin:
                if origin:
                    po.write({'origin': po.origin + ', ' + origin})
                else:
                    po.write({'origin': po.origin})
            else:
                po.write({'origin': origin})

        # Create Line
        po_line = False
        for line in po.order_line:
            if line.product_id == product_id and \
                        line.product_uom == product_id.uom_po_id and \
                        self.env.context.get('omnia_analytic_id')==line.account_analytic_id.id:
                if line._merge_in_existing_line(product_id, product_qty, product_uom, location_id, name, origin, values):
                    vals = self._update_purchase_order_line(product_id, product_qty, product_uom, values, line, partner)
                    po_line = line.write(vals)
                    break
        if not po_line:
            vals = self._prepare_purchase_order_line(product_id, product_qty, product_uom, values, po, partner)
            self.env['purchase.order.line'].sudo().create(vals)

    def _prepare_purchase_order_line(self, product_id, product_qty, product_uom, values, po, partner):
        """
        """
        values = super(StockRule, self)._prepare_purchase_order_line(product_id,
                                                                    product_qty,
                                                                    product_uom,
                                                                    values,
                                                                    po, 
                                                                    partner)
        analytic_id = self.env.context.get('omnia_analytic_id')
        if analytic_id:
            values['account_analytic_id'] = analytic_id
        orig_move_id = self.env.context.get('omnia_orig_move_id')
        if orig_move_id:
            values['omnia_mrp_orig_move'] = orig_move_id
        else:
            for _,move_id in values.get('move_dest_ids',[]):
                values['omnia_mrp_orig_move'] = move_id
                break
        return values

    def _prepare_mo_vals(self, product_id, product_qty, product_uom, location_id, name, origin, values, bom):
        out = super(StockRule, self)._prepare_mo_vals(product_id, product_qty, product_uom, location_id, name, origin, values, bom)
        orig_move_id = self.env.context.get('omnia_orig_move_id')
        if orig_move_id:
            out['omnia_mrp_orig_move'] = orig_move_id
        return out
    
    def _get_purchase_order_date(self, product_id, product_qty, product_uom, values, partner, schedule_date):
        """Return the datetime value to use as Order Date (``date_order``) for the
           Purchase Order created to satisfy the given procurement. """
        purchase_date = super(StockRule, self)._get_purchase_order_date(product_id, product_qty, product_uom, values, partner, schedule_date)
        if purchase_date < fields.Datetime.now():
            return fields.Datetime.now()
        return purchase_date
    
    # def _get_purchase_schedule_date(self, values):
    #     """Return the datetime value to use as Schedule Date (``date_planned``) for the
    #        Purchase Order Lines created to satisfy the given procurement. """
    #     schedule_date = super(StockRule, self)._get_purchase_schedule_date(values)
    #     if schedule_date < fields.Datetime.now():
    #         return fields.Datetime.now()
    #     return schedule_date
