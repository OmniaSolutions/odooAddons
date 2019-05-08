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
            'warehouse_id': self.production_id.location_src_id.get_warehouse().id,
            'production_id': self.production_id.id,
            'product_uom': sourceMoveObj.product_uom.id,
            'date_expected': sourceMoveObj.date_expected,
            'mrp_original_move': False,
            'unit_factor': unit_factor})

    def copyAndCleanLines(self, stock_move_ids, location_dest_id=None, location_source_id=None):
        outElems = []
        for stock_move_id in stock_move_ids:
            if stock_move_id.state not in ['done', 'cancel']:
                outElems.append(self.createTmpStockMove(stock_move_id, location_source_id, location_dest_id).id)
        return outElems

    @api.multi
    def button_produce_externally(self):
        values = {}
        partner = self.operation_id.default_supplier
        if not partner:
            partner = self.env['res.partner'].search([], limit=1)
        values['move_raw_ids'] = [(6, 0, self.copyAndCleanLines(self.production_id.move_raw_ids))]
        values['move_finished_ids'] = [(6, 0, self.copyAndCleanLines(self.production_id.move_finished_ids))]
        values['consume_product_id'] = self.product_id.id
        values['consume_bom_id'] = self.production_id.bom_id.id
        values['external_warehouse_id'] = self.production_id.location_src_id.get_warehouse().id
        values['production_id'] = self.production_id.id
        values['workorder_id'] = self.id
        values['request_date'] = datetime.datetime.now()
        obj_id = self.env['mrp.workorder.externally.wizard'].create(values)
        obj_id.create_vendors_from(partner)
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
        stock_move = self.env['stock.move']
        for mrp_workorder_id in self:
            picking_ids = []
            if mrp_workorder_id.state != 'external':
                continue
            stock_move_ids = stock_move.search([('mrp_workorder_id', '=', mrp_workorder_id.id)])
            for stock_move_id in stock_move_ids:
                if stock_move_id.state not in ['done', 'cancel']:
                    stock_move_id._do_unreserve()
                    stock_move_id._action_cancel()
                    picking_ids.append(stock_move_id.picking_id)
            for stock_picking_id in picking_ids:
                stock_picking_id.do_unreserve()
                stock_picking_id.action_cancel()
            mrp_workorder_id.write({'state': 'pending'})
