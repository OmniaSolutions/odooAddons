'''
Created on 12 Dec 2017

@author: mboscolo
'''
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    maintenance_id = fields.Many2one('maintenance.request', string='Maintenance')


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    #sale_amount_total = fields.Monetary(compute='_compute_sale_amount_total', string="Sum of Orders", currency_field='company_currency')
    sale_number = fields.Integer(compute='_compute_sale_amount_total', string="Number of Quotations")
    order_ids = fields.One2many('sale.order', 'maintenance_id', string='Orders')
    partner_id = fields.Many2one('res.partner', string='Customer', index=True)

    @api.depends('order_ids')
    def _compute_sale_amount_total(self):
        for maintenance in self:
            #total = 0.0
            nbr = 0
            #company_currency = self.env.user.company_id.currency_id
            for order in maintenance.order_ids:
                if order.state in ('draft', 'sent'):
                    nbr += 1
                #if order.state not in ('draft', 'sent', 'cancel'):
                #    total += order.currency_id.compute(order.amount_untaxed, company_currency)
            #maintenance.sale_amount_total = total
            maintenance.sale_number = nbr

