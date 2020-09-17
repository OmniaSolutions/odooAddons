# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models
from odoo.osv import osv
from odoo.report import report_sxw
import time

class MrpCostReport(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(MrpCostReport, self).__init__(cr, uid, name, context=context)
        self.total = 0
        self.localcontext.update({
            'time': time,
            'context': context,
            'get_mrp_code': self.get_mrp_code,
            'get_total': self.total_price,
        })
    
    def total_price(self):
        return self.total
    
    def get_mrp_code(self, product_id, project_id, level=0):
            
        def _get_rec(product_id, project_id, level, production_id, subtotal):
            
            for raw in production_id.move_raw_ids:
                res = {}
                raw_product = raw.product_id
                if raw_product not in evaluated:
                    evaluated[raw_product] = []
                res['pname'] = raw_product.name_get()[0][1]
                res['pcode'] = raw_product.default_code
                res['pqty'] = raw.product_uom_qty
                res['level'] = level
                children_productions = product_id.env['mrp.production'].search([
                    ('product_id', '=', raw_product.id),
                    ('project_id', 'in', project_id.project_ids.ids)])
                if not evaluated[raw_product]:
                    evaluated[raw_product] = children_productions.ids
                if children_productions:
                    res['unit_price'] = None
                    res['price'] = None
                else:
                    res['unit_price'] = self.getUnitPrice(product_id, raw_product.id, raw)
                    res['price'] = res['unit_price'] * res['pqty']
                    subtotal += res['price']
                result1.append(res)
                if children_productions:
                    production_child_id = evaluated[raw_product].pop(0)
                    if level < 6:
                        level += 1
                    subtotal = _get_rec(raw.product_id, project_id, level, product_id.env['mrp.production'].browse(production_child_id), subtotal)
                    if level > 0 and level < 6:
                        level -= 1
            return subtotal


        
        result = []
        production_ids = product_id.env['mrp.production'].search([('product_id', '=', product_id.id), 
                                                               ('project_id', 'in', project_id.project_ids.ids), 
                                                               ('state', '=', 'done')])
        evaluated = {}
        for production_id in production_ids:
            result1 = []
            subtotal = _get_rec(product_id, project_id, level, production_id, 0)
            res = {}
            res['production_name'] = production_id.name
            res['production_qty'] = production_id.product_qty
            res['children'] = result1
            res['subtotal'] = subtotal
            self.total += subtotal
            result.append(res)

        return result
    
    def getUnitPrice(self, product_id, raw_product, raw):
        stock_quant = product_id.env['stock.quant'].search([('product_id', '=', raw_product),
                                                            ('in_date', '<=', raw.create_date)], order="in_date desc")
        for product in stock_quant:
            if product.cost != 0:
                return product.cost
            break
        invoice_line = product_id.env['account.invoice.line'].search([('product_id', '=', raw_product),
                                                                      ('write_date', '<=', raw.create_date)], order="write_date desc")
        for product in invoice_line:
            if product.price_unit != 0:
                return product.price_unit
            break
        purchase_line = product_id.env['purchase.order.line'].search([('product_id', '=', raw_product),
                                                                      ('write_date', '<=', raw.create_date)], order="write_date desc")
        for product in purchase_line:
            if product.price_unit != 0:
                return product.price_unit
            break
        return raw.price_unit
              

class MrpCostReportAbstract(osv.AbstractModel):
    _name = 'report.omnia_mrp_analytic.report_mrp_cost'
    _inherit = 'report.abstract_report'
    _template = 'omnia_mrp_analytic.report_mrp_cost'
    _wrapped_report_class = MrpCostReport
    