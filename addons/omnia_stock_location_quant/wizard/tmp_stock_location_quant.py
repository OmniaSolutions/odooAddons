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

    @api.multi
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
    def populate_old(self, date):
        self.search([]).unlink()
        query = """SELECT a.product_id, a.location_dest_id, a.qty - b.qty FROM
                (select sum(qty_done) qty ,product_id,location_dest_id  from stock_move_line  where date < %r and state='done' group by product_id, location_dest_id) a,
                (select sum(qty_done) qty ,product_id,location_id  from stock_move_line  where date < %r and state='done' group by product_id, location_id) b
                where a.location_dest_id = b.location_id and a.product_id=b.product_id""" % (date, date)
        self.env.cr.execute(query)
        for row in self._cr.fetchall():
            self.create({'product_id': row[0],
                         'location_id': row[1],
                         'quant_qty': row[2]})
        return {
            'name': _('Stock quant'),
            'view_type': 'form',
            "view_mode": 'tree,form',
            'res_model': 'tmp.stock.location.quant',
            'target': 'main',    # current / new / inline / fullscreen / main
            'type': 'ir.actions.act_window',
            'domain': "[]"}

    @api.model
    def populate(self, date):
        self.search([]).unlink()
        query = """select sum(qty_done) qty , product_id, location_id, location_dest_id  from stock_move_line  where date < %r and state='done' group by product_id, location_id,location_dest_id
                """ % (date)
        self.env.cr.execute(query)
        out = {}
        for row in self._cr.fetchall():
            quant_qty = row[0]
            product_id = row[1]
            location_id = row[2]
            location_dest_id = row[3]
            key_negative = "%d_%d" % (location_id, product_id)
            if key_negative in out:
                out[key_negative] = out[key_negative] - quant_qty
            else:
                out[key_negative] = quant_qty * -1.0
            key_positive = "%d_%d" % (location_dest_id, product_id)
            if key_positive in out:
                out[key_positive] = out[key_positive] + quant_qty
            else:
                out[key_positive] = quant_qty
        for key, qty in out.items():
            key_split = key.split('_')
            location_id = key_split[0]
            product_id = key_split[1]
            self.create({'product_id': int(product_id),
                         'location_id': int(location_id),
                         'quant_qty': qty * 1.0})

        return {
            'name': _('Stock quant'),
            'view_type': 'form',
            "view_mode": 'tree,form',
            'res_model': 'tmp.stock.location.quant',
            'target': 'main',    # current / new / inline / fullscreen / main
            'type': 'ir.actions.act_window',
            'domain': "[]"}