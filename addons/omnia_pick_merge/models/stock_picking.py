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
        for move_line in self.move_lines:
            old_move = self.env['stock.move'].search([('id', '=', move_line.from_move_id)])
            old_move.product_uom_qty = old_move.product_uom_qty + move_line.product_uom_qty
        self.mapped('move_lines')._action_cancel()
        self.write({'is_locked': True})
        return True

#     @api.multi
#     def unlink(self):
#         self.mapped('move_lines')._action_cancel()
#         self.mapped('move_lines').unlink() # Checks if moves are not done
#         return super(Picking, self).unlink()
