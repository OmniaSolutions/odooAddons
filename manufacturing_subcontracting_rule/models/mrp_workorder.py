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
    is_mo_produced = fields.Boolean('Is Manufacturing Produced')
    before_state = fields.Char('Before state')

    def createTmpStockMove(self, sourceMoveObj, location_source_id=None, location_dest_id=None):
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
            'date_expected': sourceMoveObj.forecast_expected_date,
            'mrp_original_move': False,
            'workorder_id': self.id,
            })

    def get_wizard_value(self):
        values = {'warnings_msg': ''}
        raw_lines = []
        finish_lines = []
        production = self.production_id
        for raw_move in self.production_id.move_raw_ids:
            if raw_move.bom_line_id.operation_id == self.operation_id:
                location_source_id = raw_move.location_id.id
                location_dest_id = raw_move.location_dest_id.id
                raw_move_new = production.createTmpStockMove(
                    raw_move,
                    location_source_id,
                    location_dest_id
                    )
                raw_lines.append(raw_move_new.id)
                finish_move_new = production.createTmpStockMove(
                    raw_move,
                    location_dest_id,
                    location_source_id,
                    )
                finish_lines.append(finish_move_new.id)
            elif not raw_move.bom_line_id.operation_id:
                values['warnings_msg'] += '''
                <div style="color:#ff5400;">
                Bom line %r has not "Consumed in operation" field setup.
                </div>
                ''' % (raw_move.bom_line_id.display_name)
            else:
                values['warnings_msg'] += '''
                <div style="color:#ff5400;">
                Bom line operation [%s] %s and workorder operation [%s] %s are different for line %s
                </div>''' % (self.operation_id.id,
                             self.operation_id.display_name,
                             raw_move.bom_line_id.operation_id.id,
                             raw_move.bom_line_id.operation_id.display_name,
                             raw_move.bom_line_id.display_name,
                             )
        if raw_lines or finish_lines:
            values['warnings_msg'] = ''
        values['move_raw_ids'] = [(6, 0, raw_lines)]
        values['move_finished_ids'] = [(6, 0, finish_lines)]
        values['production_id'] = production.id
        values['consume_bom_id'] = production.bom_id.id
        values['workorder_id'] = self.id
        return values

    def button_produce_externally(self):
        values = self.get_wizard_value()
        obj_id = self.env["mrp.workorder.externally.wizard"].create(values)
        partner = self.operation_id.default_supplier
        if not partner:
            raise UserError("No Partner set to Routing Operation")
        obj_id.create_vendors_from(partner)
        obj_id._request_date()
        self.before_state = self.state
        self.env.cr.commit()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.workorder.externally.wizard',
            'view_mode': 'form,tree',
            'view_type': 'form',
            'res_id': obj_id.id,
            'context': {'wizard_id': obj_id.id},
            'target': 'new',
        }

    def button_cancel_produce_externally(self):
        for mrp_workorder_id in self:
            pickings = mrp_workorder_id.getExternalPickings()
            for pick in pickings:
                if pick.state in ('assigned', 'confirmed', 'partially_available', 'draft', 'waiting'):
                    pick.action_cancel()
            ext_purchase = mrp_workorder_id.getExternalPurchase()
            for purchase in ext_purchase:
                if purchase.state in ('draft', 'to_approve', 'sent', 'purchase'):
                    purchase._compute_picking()
                    purchase.button_cancel()
            mrp_workorder_id.state = mrp_workorder_id.before_state or 'draft'
            mrp_workorder_id.before_state = ''

    def copyAndCleanLines(self, stock_move_ids, location_dest_id=None, location_source_id=None):
        outElems = []
        for stock_move_id in stock_move_ids:
            if stock_move_id.state not in ['done', 'cancel']:
                outElems.append(self.createTmpStockMove(stock_move_id, location_source_id, location_dest_id).id)
        return outElems

    def updateProducedQty(self, newQty):
        for woBrws in self:
            alreadyProduced = woBrws.qty_produced
            # FIXME: Se ne produco piu' del dovuto?
            woBrws.qty_produced = alreadyProduced + newQty

    def checkRecordProduction(self):
        for woBrws in self:
            if woBrws.qty_produced >= woBrws.qty_production:
                woBrws.button_finish()

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

    def getExternalPickings(self):
        pickObj = self.env['stock.picking']
        for woBrws in self:
            return pickObj.search([('sub_workorder_id', '=', woBrws.id)])
        return pickObj

    def open_external_pickings(self):
        newContext = self.env.context.copy()
        picks = self.getExternalPickings()
        return {'name': _("External Pickings"),
                'views': [(False, 'tree')],
                'view_id': self.env.ref('stock.vpicktree').id,
                'target': 'current',
                'view_mode': 'tree,form',
                'res_model': 'stock.picking',
                'type': 'ir.actions.act_window',
                'context': newContext,
                'domain': [('id', 'in', picks.ids)],
        }

    def getExternalPurchase(self):
        picks = self.env['purchase.order']
        for woBrws in self:
            picks = picks.search([('workorder_external_id', '=', woBrws.id)])
        return picks
    
    def open_external_purchase(self):
        newContext = self.env.context.copy()
        picks = self.getExternalPurchase()
        return {
            'name': _("External Pickings"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'context': newContext,
            'domain': [('id', 'in', picks.ids)],
        }
