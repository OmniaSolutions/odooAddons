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

    @api.multi
    def button_produce_externally(self):
        values = self.production_id.get_wizard_value()
        values['work_order_id'] = self.id
        obj_id = self.env['mrp.externally.wizard'].create(values)
        obj_id.create_vendors(self.production_id, self)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.externally.wizard',
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

    @api.multi
    def updateProducedQty(self, newQty):
        for woBrws in self:
            alreadyProduced = woBrws.qty_produced
            #FIXME: Se ne produco piu' del dovuto?
            woBrws.qty_produced = alreadyProduced + newQty
    
    @api.multi
    def checkRecordProduction(self):
        for woBrws in self:
            if woBrws.qty_produced >= woBrws.qty_production:
                woBrws.button_finish()
        
    @api.multi
    def button_finish(self):
        res = super(MrpWorkorder, self).button_finish()
        production_id = self.production_id
        isExternal = False
        for relatedWO in self.search([('production_id', '=', production_id.id)]):
            # Check if external workorder
            if relatedWO.getExternalPickings():
                isExternal = True
                break
        if not self.next_work_order_id and isExternal:
            # Close manufacturing order
            production_id.write({'state': 'done', 'date_finished': fields.Datetime.now()})
        return res

    @api.multi
    def getExternalPickings(self):
        pickObj = self.env['stock.picking']
        for woBrws in self:
            return pickObj.search([('sub_workorder_id', '=', woBrws.id)])
        return pickObj

    @api.multi
    def open_external_pickings(self):
        newContext = self.env.context.copy()
        picks = self.getExternalPickings()
        return {
            'name': _("External Pickings"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'context': newContext,
            'domain': [('id', 'in', picks.ids)],
        }