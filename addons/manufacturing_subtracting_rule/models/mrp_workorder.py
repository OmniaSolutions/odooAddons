'''
Created on 16 Jan 2018

@author: mboscolo
'''

from odoo import models
from odoo import fields
from odoo import api
from odoo import _
import logging
import datetime


class MrpWorkorder(models.Model):
    _inherit = ['mrp.workorder']
    external_partner = fields.Many2one('res.partner', string='External Partner')
    state = fields.Selection(selection_add=[('external', 'External Production')])
    # date_planned_finished
    # date_planned_start
    # gestire gli scrap

    @api.multi
    def button_produce_externally(self):
        print 'launch workorder'
        values = {}
        values['external_partner'] = self.operation_id.default_supplier.id
        values['move_raw_ids'] = [(6, 0, self.production_id.move_raw_ids.ids)]
        values['move_finished_ids'] = [(6, 0, self.production_id.move_finished_ids.ids)]
        obj_id = self.env['mrp.workorder.externally.wizard'].create(values)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.workorder.externally.wizard',
            'view_mode': 'form,tree',
            'view_type': 'form',
            'res_id': obj_id.id,
            'target': 'new',
        }

    @api.multi
    def button_cancel_produce_externally(self):
        stockPickingObj = self.env['stock.picking']
        for workOrderBrws in self:
            # qui e da sistemare per il work order
            stockPickList = stockPickingObj.search([('origin', '=', workOrderBrws.name)])
            for pickBrws in stockPickList:
                pickBrws.action_cancel()
            workOrderBrws.write({'state': 'pending'})
