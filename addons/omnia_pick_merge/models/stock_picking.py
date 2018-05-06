'''
Created on 26 Apr 2018

@author: mboscolo
'''
from datetime import datetime
from odoo import models
from odoo import fields
from odoo import api
from odoo import _


class stock_picking_custom(models.Model):
    _inherit = 'stock.picking'
    _name = 'stock.picking'

    from_stock_id = fields.Many2one('stock.picking', string='Related move', index=True)
    merged_pick_ids = fields.One2many('stock.picking', 'from_stock_id', string=_('Merge'))
