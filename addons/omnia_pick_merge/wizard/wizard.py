'''
Created on 26 Apr 2018

@author: mboscolo
'''

import math
import logging
import datetime
from dateutil.relativedelta import relativedelta

from odoo import models
from odoo import fields
from odoo import api
from odoo import _
from odoo import tools
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class TmpStockMoveLine(models.TransientModel):
    _name = "stock.tmp_merge_pick_line"
    ref_stock_move_id = fields.Integer(string=_('Reference Move'))
    product_name = fields.Char(_('Product'))
    sale_order_line_id = fields.Integer(_('Reference Sale Order Line'))
    move_quantity = fields.Float(_('Move Quantity'), )
    merge_quantity = fields.Float(_('Quantity'))
    ref_id = fields.Many2one('stock.tmp_merge_pick')


class TmpStockMove(models.TransientModel):
    _name = "stock.tmp_merge_pick"

    ref_stock_move = fields.One2many('stock.tmp_merge_pick_line',
                                     'ref_id',
                                     string=_('Lines'))
    location_id = fields.Integer(string=_('Stock location id'))
    location_dest_id = fields.Integer(string=_('Customer location id'))
    partner_id = fields.Integer(string=_('Partner id'))
    picking_type_id = fields.Integer(string=_('Picking id'))
    pick_origin = fields.Text(_('Source'))

    @api.model
    def populateFromPick(self, pick_ids):
        pick_ids = self.env['stock.picking'].browse(pick_ids)
        first_partner_id = -1
        for pick_id in pick_ids:
            if first_partner_id == -1:
                first_partner_id = pick_id.partner_id.id
                self.location_id = pick_id.location_id.id
                self.partner_id = pick_id.partner_id.id
                self.location_dest_id = pick_id.location_dest_id.id
                self.picking_type_id = pick_id.picking_type_id.id
                self.pick_origin = pick_id.origin
                continue
            if first_partner_id != pick_id.partner_id.id:
                raise UserError(_("Partner are not equal"))
            self.pick_origin = self.pick_origin + "," + pick_id.origin
        for pick_id in pick_ids:
            for move in pick_id.move_lines:
                if move.product_id:
                    self.ref_stock_move = (0, 0, {'ref_id': self.id,
                                                  'ref_stock_move_id': move.id,
                                                  'product_name': move.product_id.display_name,
                                                  'sale_order_line_id': move.sale_line_id.id,
                                                  'move_quantity': move.product_qty,
                                                  'merge_quantity': move.product_qty})

    @api.multi
    def button_merge_picking(self):
        out_pick = self.env['stock.picking'].create({
            'location_id': self.location_id,
            'location_dest_id': self.location_dest_id,
            'partner_id': self.partner_id,
            'picking_type_id': self.picking_type_id,
            'origin': self.pick_origin
        })
        tmpl_move = self.env['stock.move']
        for pick_line in self.ref_stock_move:
            old_move_id = tmpl_move.search([('id', '=', pick_line.ref_stock_move_id)])
            old_move_id.copy({'picking_id': out_pick.id,
                              'product_uom_qty': pick_line.merge_quantity})
            if old_move_id.product_qty != pick_line.merge_quantity:
                if old_move_id.product_qty < pick_line.merge_quantity:
                    raise UserError(_('Unable to set quantity less then 0'))
                old_move_id.copy({'product_uom_qty': old_move_id.product_qty - pick_line.merge_quantity})
            old_move_id._action_cancel()
            if old_move_id.picking_id not in out_pick.merged_pick_ids:
                out_pick.merged_pick_ids = [(4, old_move_id.picking_id.id)]

        return {
            'name': _("New Move"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', out_pick.ids)],
        }
