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

    @api.multi
    def _picking_ids(self):
        pickings = self.env['stock.picking']
        move = self.env['stock.move']
        for order in self:
            move_ids = move.search([('sale_line_id', 'in', order.order_line.ids)])
            pickings = move_ids.mapped('picking_id')
            order.picking_ids = pickings
            order.picking_count = len(pickings)
    picking_ids = fields.Many2many('stock.picking', compute=_picking_ids)
