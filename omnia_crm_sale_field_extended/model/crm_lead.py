'''
Created on 3 Apr 2017

@author: mboscolo
'''
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
import logging


class crm_lead(models.Model):
    '''
    extent the base class adding some new feature
    '''
    _name = "crm.lead"
    _inherit = ['crm.lead']
    sale_order_amount = fields.Float(compute='_compute_order_non_confirmed', tracking=True)
    sale_order_amount_confirmed = fields.Float(compute='_compute_order_confirmed', tracking=True)
    sale_probability_group = fields.Char("Probability %", default="30")

    def getProbabilityRange(self, value):
        if value <= 30:
            return "0"
        if value > 30 and value <= 49:
            return "30"
        if value > 50 and value <= 79:
            return "50"
        if value >= 80:
            return "80"

    @api.onchange("probability")
    def compute_range(self):
        self.sale_probability_group = self.getProbabilityRange(self.probability)

    @api.multi
    def _compute_probability_group(self):
        for crm_opp in self:
            crm_opp.sale_probability_group = self.getProbability(crm_opp.probability)

    @api.multi
    def _compute_order_non_confirmed(self):
        for crm_opp in self:
            out = 0
            for opp in self.env['sale.order'].search([('opportunity_id', '=', crm_opp.id), ('state', 'in', ['draft', 'sent'])]):
                out = out + opp.amount_untaxed
            crm_opp.sale_order_amount = out

    @api.multi
    def _compute_order_confirmed(self):
        for crm_opp in self:
            out = 0
            for opp in self.env['sale.order'].search([('opportunity_id', '=', crm_opp.id), ('state', 'in', ['sale', 'done'])]):
                out = out + opp.amount_untaxed
            crm_opp.sale_order_amount

crm_lead()
