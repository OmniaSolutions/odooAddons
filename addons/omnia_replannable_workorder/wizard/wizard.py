'''
Created on 16 Jan 2018

@author: mboscolo
'''
from odoo.addons import decimal_precision as dp
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
import logging
import datetime
from dateutil.relativedelta import relativedelta


class ChangeProductMoveWizard(models.TransientModel):
    _name = "change_product_move_wizard"

    stock_moves = fields.Many2many('stock.move')
    product_id = fields.Many2one('product.product',
                                 'New Product')

    def changeProduct(self):
        for move in self.stock_moves:
            if move.state not in ['cancelled', 'done']:
                move.product_id = self.product_id

    @api.multi
    def ShowWizard(self, ids):
        new_me = self.create({})
        workorder_ids = self.env['mrp.workorder'].search([('id', 'in', ids)])
        for workorder_id in workorder_ids:
            for move_id in workorder_id.production_id.move_raw_ids:
                if move_id.state not in ['done', 'cancelled']:
                    new_me.stock_moves = [(4, move_id.id)]

        action = {'name': 'Change Raw product',
                  'view_type': 'form',
                  'view_mode': 'form',
                  'target': 'new',
                  'res_id': new_me.id,
                  'res_model': 'change_product_move_wizard',
                  'type': 'ir.actions.act_window'}
        return action
