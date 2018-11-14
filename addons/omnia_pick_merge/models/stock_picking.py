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

    from_stock_id = fields.Many2one('stock.picking', string='Related move', index=True)
    merged_pick_ids = fields.One2many('stock.picking', 'from_stock_id', string=_('Merge'))

    @api.multi
    def action_cancel(self):
        for pickBrws in self:
            for move_line in pickBrws.move_lines:
                old_move = self.env['stock.move'].search([('id', '=', move_line.from_move_id)])
                if old_move:
                    old_move.product_uom_qty = old_move.product_uom_qty + move_line.product_uom_qty
            pickBrws.mapped('move_lines').action_cancel()
            pickBrws.write({'is_locked': True})
        return super(stock_picking_custom, self).action_cancel()
