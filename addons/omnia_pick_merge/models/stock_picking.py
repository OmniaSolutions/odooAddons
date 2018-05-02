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
    _name = 'stock.picking'

    merged_pick = fields.Many2many('stock.picking',
                                   string=_('Merged Picking'))

    @api.multi
    def show_merge(self):
        ids = self.ids
        if len(ids) < 1:
            return False
        tmp_item = self.env['stock.tmp_merge_pick']
        obj_merge_tmp = tmp_item.create()
        obj_merge_tmp.populateFromPick(self.ids)
        return {
            'name': _("Merge Picking"),
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.ids[0],
            'res_model': 'stock.tmp_merge_pick',
            'type': 'ir.actions.act_window'
        }
