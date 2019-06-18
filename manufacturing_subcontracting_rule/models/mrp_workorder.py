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
from odoo.exceptions import UserError


class MrpWorkorder(models.Model):
    _inherit = ['mrp.workorder']
    external_partner = fields.Many2one('res.partner', string='External Partner')
    state = fields.Selection(selection_add=[('external', 'External Production')])
    external_product = fields.Many2one('product.product',
                                       string=_('External Product use for external production'))
    is_mo_produced = fields.Boolean('Is Manufacturing Produced')

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

    @api.model
    def createWizard(self):
        values = self.production_id.get_wizard_value()
        partner = self.operation_id.default_supplier
        if self.operation_id.external_operation and not partner:
            raise UserError("No Partner set to Routing Operation")
        values['consume_product_id'] = self.product_id.id
        values['consume_bom_id'] = self.production_id.bom_id.id
        values['external_warehouse_id'] = self.production_id.location_src_id.get_warehouse().id
        values['work_order_id'] = self.id
        obj_id = self.env['mrp.externally.wizard'].create(values)
        obj_id.create_vendors_from(partner)
        return obj_id

    @api.multi
    def button_produce_externally(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.externally.wizard',
            'view_mode': 'form,tree',
            'view_type': 'form',
            'res_id': self.createWizard().id,
            'target': 'new',
        }

    @api.multi
    def button_cancel_produce_externally(self):
        stockPickingObj = self.env['stock.picking']
        for workOrderBrws in self:
            stockPickList = stockPickingObj.search([('origin', '=', workOrderBrws.name)])
            stockPickList += workOrderBrws.getExternalPickings()
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
            woBrws.qty_produced = woBrws.qty_production
            woBrws.record_production()
            if not woBrws.next_work_order_id:
                woBrws.production_id.post_inventory()
                woBrws.production_id.button_mark_done()

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

    @api.multi
    def updateQtytoProduce(self, new_qty):
        self.qty_production = new_qty
        self.production_id.updateQtytoProduce(new_qty)

    @api.model
    def isPicksInDone(self):
        isOut = False
        for stock_picking in self.getExternalPickings():
            if stock_picking.isIncoming(stock_picking):
                if stock_picking.state == 'cancel':
                    isOut = True
                    continue
                if stock_picking.state != 'done':
                    return False
                else:
                    isOut = True
        return isOut

    @api.multi
    def closeWO(self):
        for wo_id in self:
            wo_id.qty_produced = wo_id.qty_production
            wo_id.record_production()
            
    @api.multi
    def produceQty(self, qty_to_produce):
        for wo_id in self:
            wo_id.qty_producing = qty_to_produce
            wo_id.record_production()
