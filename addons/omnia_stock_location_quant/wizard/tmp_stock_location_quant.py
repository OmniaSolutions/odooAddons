'''
Created on Sep 25, 2018

@author: mboscolo
'''
import logging
import datetime

from odoo import models
from odoo import fields
from odoo import api
from odoo import _
from odoo import tools
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class TmpChooseDate(models.TransientModel):
    _name = "tmp.choose.date"
    date = fields.Date("Inventoty Date")

    @api.one
    def action_show_quant(self):
        res = self.env['tmp.stock.location.quant'].populate(self.date)
        return res


class TmpStockLocationQuant(models.TransientModel):
    _name = "tmp.stock.location.quant"

    product_id = fields.Many2one(
        'product.product',
        'Product')
    location_id = fields.Many2one('stock.location')
    quant_qty = fields.Float('Quantity')

    @api.model
    def populate(self, date):
        self.search([]).unlink()
        query = """SELECT a.product_id, a.location_dest_id, a.qty - b.qty FROM
                (select sum(qty_done) qty ,product_id,location_dest_id  from stock_move_line  where date < %r group by product_id, location_dest_id) a,
                (select sum(qty_done) qty ,product_id,location_id  from stock_move_line  where date < %r group by product_id, location_id) b
                where a.location_dest_id = b.location_id and a.product_id=b.product_id""" % (date, date)
        self.env.cr.execute(query)
        for row in self._cr.fetchall():
            self.create({'product_id': row[0],
                         'location_id': row[1],
                         'quant_qty': row[2]})
            break
        return {
            'name': _('Stock quant'),
            'view_type': 'form',
            "view_mode": 'tree',
            'res_model': 'tmp.stock.location.quant',
            'target': 'current',
            'type': 'ir.actions.act_window',
            'domain': "[]"}
