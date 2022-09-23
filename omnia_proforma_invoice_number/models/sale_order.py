'''
Created on 5 Jun 2018

@author: mboscolo
'''
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    proforma_number = fields.Char("ProForma Number",
                                  help="""
                                  Assing a pro forma number to the sale order
                                  """)
    
    def assign_pro_forma_number(self):
        for sale_order in self:
            sale_order.proforma_number = self.env['ir.sequence'].next_by_code('pro.forma.number')
