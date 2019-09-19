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
    #sale_order_line_id = fields.Integer(_('Reference Sale Order Line'))
    procurement_id = fields.Integer('Procurement')
    sale_order_name = fields.Char(_('Order Ref'))
    sale_order_customer_name = fields.Char(_('Customer Name'))
    move_quantity = fields.Float(_('Move Quantity'), )
    product_uom_qty = fields.Float(_('Requested Quantity'), readonly=True)
    ref_id = fields.Many2one('stock.tmp_merge_pick')
    requested_date = fields.Datetime(_('Request date'))
    date_expected = fields.Datetime(_('Effective date'))
    identificated = fields.Boolean(_('Identificato'))
    qty_on_hand = fields.Float(_('Quantity on hand '))


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
    validate = fields.Boolean(_('Auto validate'),
                              default=False)

    @api.model
    def populateFromPick(self, pick_ids):
        pick_ids.sort()
        tmp_pick_ids = self.env['stock.picking'].browse(pick_ids)
        good_pick_list = []
        for pick_brws in tmp_pick_ids:
            if pick_brws.state not in ['done', 'cancel']:
                good_pick_list.append(pick_brws)
        if len(good_pick_list) <= 1:
            raise UserError(_('You have only one available picking to merge. Merge operation is aborted'))
        TmpStockMoveLineObj = self.env['stock.tmp_merge_pick_line']
        first_partner_id = -1
        for pick_brws in good_pick_list:
            if pick_brws.picking_type_id.code == 'incoming':
                raise UserError(_("Merge incoming pickings is not allowed."))
            if first_partner_id == -1:
                first_partner_id = pick_brws.partner_id.id
                self.location_id = pick_brws.location_id.id
                self.partner_id = pick_brws.partner_id.id
                self.location_dest_id = pick_brws.location_dest_id.id
                self.picking_type_id = pick_brws.picking_type_id.id
                self.pick_origin = pick_brws.origin
                continue
            if first_partner_id != pick_brws.partner_id.id:
                raise UserError(_("Partner are not equal"))
            if self.pick_origin or pick_brws.origin:
                self.pick_origin = str(self.pick_origin or '') + "," + str(pick_brws.origin or '')

        product_qty_assigned = {}
        logging.info('good_pick_list: %r' % (good_pick_list))
        for pick_brws in good_pick_list:
            if pick_brws.state in ['done', 'cancel']:
                raise UserError(_('You cannot merge picking not in Done or Cancel states.'))
                continue
            for move in pick_brws.move_lines:
                if move.state in ['done', 'cancel']:
                    continue
                product_id = move.product_id
                if product_id:
                    used_qty = 0
                    qty_already_done = move.quantity_done
                    needed_qty = move.product_qty - qty_already_done
                    if product_id.id not in product_qty_assigned:
                        product_qty_assigned[product_id.id] = product_id.qty_available
                    residual_qty = product_qty_assigned[product_id.id] - needed_qty
                    if residual_qty >= 0:
                        product_qty_assigned[product_id.id] = residual_qty
                        used_qty = move.product_qty
                    else:
                        used_qty = product_qty_assigned[product_id.id]
                        product_qty_assigned[product_id.id] = 0
                    saleOrder = move.getSaleOrder(move)
                    TmpStockMoveLineObj.create({'ref_id': self.id,
                                                'ref_stock_move_id': move.id,
                                                'product_name': move.product_id.display_name,
                                                #'sale_order_line_id': move.sale_line_id.id,
                                                'product_uom_qty': move.product_uom_qty,
                                                'move_quantity': needed_qty,
                                                'requested_date': move.date,
                                                'date_expected': move.date_expected,
                                                'sale_order_name': saleOrder.name,
                                                'sale_order_customer_name': saleOrder.partner_id.name,
                                                'procurement_id': move.procurement_id.id,
                                                'qty_on_hand': used_qty})

    @api.multi
    def merge_picks(self, only_available=False):
        out_pick = self.env['stock.picking'].create({
            'location_id': self.location_id,
            'location_dest_id': self.location_dest_id,
            'partner_id': self.partner_id,
            'picking_type_id': self.picking_type_id,
            'origin': self.pick_origin
        })
        tmpl_move = self.env['stock.move']
        for pick_line in self.ref_stock_move:
            if only_available:
                if pick_line.qty_on_hand <= 0:
                    continue
                move_quanity = pick_line.qty_on_hand
            else:
                move_quanity = pick_line.move_quantity
            old_move_id = tmpl_move.search([('id', '=', pick_line.ref_stock_move_id)])
            if old_move_id.product_qty != pick_line.move_quantity:
                if old_move_id.product_qty < pick_line.move_quantity:
                    raise UserError(_('Unable to set quantity less then 0'))
            old_move_id.copy({'picking_id': out_pick.id,
                              'from_move_id': old_move_id.id,
                              'product_uom_qty': move_quanity,
                              'procure_method': 'make_to_stock'})
            if old_move_id.picking_id not in out_pick.merged_pick_ids:
                out_pick.merged_pick_ids = [(4, old_move_id.picking_id.id)]
            old_move_id.write({'product_uom_qty': old_move_id.product_qty - move_quanity})
            if old_move_id.product_qty == 0:
                old_move_id.action_cancel()
        if self.validate:
            out_pick.action_confirm()
        for pick in out_pick.merged_pick_ids:
            msg = 'This picking has been merged in picking %r' % (out_pick.display_name)
            pick.message_post(msg)
        return {
            'name': _("New Pick"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', out_pick.ids)],
        }

    @api.multi
    def button_merge_picking(self):
        return self.merge_picks()

    @api.multi
    def button_merge_picking_available(self):
        return self.merge_picks(True)
