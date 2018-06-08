'''
Created on 8 Jun 2018

@author: mboscolo
'''

from odoo import models
from odoo import fields
from odoo import api
from odoo import _
import logging


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'
    allow_ddt = fields.Boolean(string=_("Allow ddt Number"))
