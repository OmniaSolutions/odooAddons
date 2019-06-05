'''
Created on 26 Apr 2018

@author: mboscolo
'''
from datetime import datetime
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
from odoo.exceptions import UserError


class stock_picking_custom(models.Model):
    _inherit = 'stock.picking'

    from_stock_id = fields.Many2one('stock.picking', string='Related move', index=True)
    merged_pick_ids = fields.One2many('stock.picking', 'from_stock_id', string=_('Merge'))

    @api.multi
    def action_cancel(self):
        msg = ''
        for merged_pick in self:
            if merged_pick.state == 'cancel':
                continue
            for move_line in merged_pick.move_lines:
                old_move = self.env['stock.move'].search([('id', '=', move_line.from_move_id)])
                if old_move:
                    if old_move.state in ['draft', 'waiting', 'confirmed', 'cancel'] and old_move.picking_id.state in ['draft', 'waiting', 'confirmed', 'cancel']:
                        old_move.product_uom_qty = old_move.product_uom_qty + move_line.product_uom_qty
                        old_move.state = 'draft'
                    else:
                        msg += "\nOriginal picking %r has not been restored due to state" % (old_move.picking_id.display_name)
            merged_pick.mapped('move_lines').action_cancel()
            merged_pick.write({'is_locked': True})
        res = super(stock_picking_custom, self).action_cancel()
        self.env.cr.commit()
        if msg:
            raise UserError(msg)
        return res

    @api.multi
    def unlink(self):
        for pickBrws in self:
            if pickBrws.merged_pick_ids:
                pickBrws.action_cancel()
        return super(stock_picking_custom, self).unlink()
