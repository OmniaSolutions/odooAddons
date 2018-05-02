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


class TmpStockMoveLine(models.Model):
    _name = "stock.tmp_merge_pickLine"
    ref_stock_move = fields.Many2one('stock_move',
                                     _('Reference Move'))
    product_id = fields.Many2one(related='ref_stock_move.product_id')
    move_quantity = fields.Float(related='ref_stock_move.product_uom_qty')
    sale_order = fields.Many2one(related='ref_stock_move.picking_id.sale_id')
    merge_quantity = fields.Float(_('Quantity'))


class TmpStockMove(models.Model):
    _name = "stock.tmp_merge_pick"

    ref_stock_move = fields.Many2one('stock.tmp_merge_pickLine',
                                     _('Lines'))

    @api.model
    def populateFromPick(self, picks):
        tmp_item = self.env['stock.TmpStockMoveLine']
        for pick in picks:
            item_id = tmp_item.create({'ref_stock_move': pick.id})
            self.ref_stock_move = [(6, 0, item_id.ids)]
