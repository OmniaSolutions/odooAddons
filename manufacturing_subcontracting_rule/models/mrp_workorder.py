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

    def createTmpStockMove(self, sourceMoveObj, location_source_id=None, location_dest_id=None, unit_factor=1.0):
        tmpMoveObj = self.env["stock.tmp_move"]
        if not location_source_id:
            location_source_id = sourceMoveObj.location_id.id
        if not location_dest_id:
            location_dest_id = sourceMoveObj.location_dest_id.id
        return tmpMoveObj.create({
            'name': sourceMoveObj.name,
            'company_id': sourceMoveObj.company_id.id,
            'product_id': sourceMoveObj.product_id.id,
            'product_uom_qty': sourceMoveObj.product_uom_qty,
            'location_id': location_source_id,
            'location_dest_id': location_dest_id,
            'partner_id': self.external_partner.id,
            'note': sourceMoveObj.note,
            'state': 'draft',
            'origin': sourceMoveObj.origin,
            'warehouse_id': self.location_src_id.get_warehouse().id,
            'production_id': self.id,
            'product_uom': sourceMoveObj.product_uom.id,
            'date_expected': sourceMoveObj.date_expected,
            'mrp_original_move': False,
            'unit_factor': unit_factor})

    def copyAndCleanLines(self, brwsList, location_dest_id=None, location_source_id=None):
        outElems = []
        for elem in brwsList:
            outElems.append(self.createTmpStockMove(elem, location_source_id, location_dest_id).id)
        return outElems

    @api.multi
    def button_produce_externally(self):
        raise Exception("Function not implemented !!")
        values = {}
        partner = self.operation_id.default_supplier
        if not partner:
            partner = self.env['res.partner'].search([], limit=1)
        values['move_raw_ids'] = [(6, 0, self.copyAndCleanLines(self.move_raw_ids))]
        values['move_finished_ids'] = [(6, 0, self.copyAndCleanLines(self.move_finished_ids))]
        values['consume_product_id'] = self.product_id.id
        values['consume_bom_id'] = self.bom_id.id
        values['external_warehouse_id'] = self.location_src_id.get_warehouse().id
        values['production_id'] = self.id
        values['request_date'] = datetime.datetime.now()
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
