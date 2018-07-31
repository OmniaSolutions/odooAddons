'''
Created on 5 Jun 2018

@author: dsmerghetto
'''
from odoo import fields
from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    recycle_id = fields.Many2one('stock.recycle_product')
