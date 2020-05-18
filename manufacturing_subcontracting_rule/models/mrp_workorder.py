'''
Created on 16 Jan 2018

@author: mboscolo
'''

from odoo import models
from odoo import fields
from odoo import api
from odoo.exceptions import UserError
from odoo import _
import logging
import datetime


class MrpWorkorder(models.Model):
    _inherit = ['mrp.workorder']
    external_partner = fields.Many2one('res.partner', string='External Partner')
    state = fields.Selection(selection_add=[('external', 'External Production')])
    external_product = fields.Many2one('product.product',
                                       string=_('External Product use for external production'))

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

    @api.model
    def createWizard(self):
        values = self.production_id.get_wizard_value()
        partner = self.operation_id.default_supplier
        if not partner:
            raise UserError("No Partner set to Routing Operation")
        values['consume_product_id'] = self.product_id.id
        values['consume_bom_id'] = self.production_id.bom_id.id
        values['external_warehouse_id'] = self.production_id.location_src_id.get_warehouse().id
        values['workorder_id'] = self.id
        mrp_workorder_externally_wizard_id = self.env['mrp.workorder.externally.wizard'].create(values)
        mrp_workorder_externally_wizard_id.create_vendors_from(partner)
        return mrp_workorder_externally_wizard_id

    @api.multi
    def button_produce_externally(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.workorder.externally.wizard',
            'view_mode': 'form,tree',
            'view_type': 'form',
            'res_id': self.createWizard().id,
            'target': 'new',
        }

    @api.multi
    def button_cancel_produce_externally(self):
        stock_move = self.env['stock.move']
        for mrp_workorder_id in self:
            picking_ids = []
            if mrp_workorder_id.state != 'external':
                continue
            stock_move_ids = stock_move.search(['|', ('mrp_workorder_id', '=', mrp_workorder_id.id), ('workorder_id', '=', mrp_workorder_id.id)])
            for stock_move_id in stock_move_ids:
                if stock_move_id.state not in ['done', 'cancel']:
                    stock_move_id._do_unreserve()
                    stock_move_id._action_cancel()
                    picking_ids.append(stock_move_id.picking_id)
            for stock_picking_id in picking_ids:
                stock_picking_id.do_unreserve()
                stock_picking_id.action_cancel()
            purchase_ids = self.env['purchase.order'].search([('workorder_external_id', '=', mrp_workorder_id.id)])
            for purchase in purchase_ids:
                purchase.button_cancel()
                purchase.unlink()
            mrp_workorder_id.write({'state': 'ready'})

    def copyAndCleanLines(self, stock_move_ids, location_dest_id=None, location_source_id=None):
        outElems = []
        for stock_move_id in stock_move_ids:
            if stock_move_id.state not in ['done', 'cancel']:
                outElems.append(self.createTmpStockMove(stock_move_id, location_source_id, location_dest_id).id)
        return outElems

    @api.multi
    def updateProducedQty(self, newQty):
        for woBrws in self:
            alreadyProduced = woBrws.qty_produced
            # FIXME: Se ne produco piu' del dovuto?
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

    @api.multi
    def open_external_purchase(self):
        newContext = self.env.context.copy()
        picks = self.env['purchase.order']
        for woBrws in self:
            picks = picks.search([('workorder_external_id', '=', woBrws.id)])
        return {
            'name': _("External Pickings"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'context': newContext,
            'domain': [('id', 'in', picks.ids)],
        }
