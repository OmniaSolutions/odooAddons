'''
Created on 18 Jul 2018

@author: mboscolo
'''
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round, float_is_zero
from datetime import datetime
from odoo import models
from odoo import fields
from odoo import _
from odoo import api
import math
import logging


class ChangeProductionQty(models.TransientModel):
    _inherit = "change.production.qty"

    @api.multi
    def change_prod_qty_external(self, productionBrws):
        raise UserError(_('You cannot change manufacturing order quantity if you are producing it externally. Cancel the external production and update the quantity.'))

    @api.multi
    def change_prod_qty_mold(self, production):
        super(ChangeProductionQty, self).change_prod_qty()
        production.onChangeProductQty()
        evaluatedMoves = []
        n_shut = production.product_qty / production.getNImpronte(production.product_id)
        for cavity in production.mold_id.mold_configuration:
            if not cavity.exclude:
                for bom_id in cavity.product_id.bom_ids:
                    _boms, exploded_lines = bom_id.explode(cavity.product_id,
                                                           1,  # factor
                                                           picking_type=bom_id.picking_type_id)
                    for bom_line, line_data in exploded_lines:
                        moves = production.move_raw_ids.filtered(lambda x: x.bom_line_id.id == bom_line.id and x.state not in ('done', 'cancel'))
                        for move in moves:
                            if not move.is_materozza:
                                beforeOrdered = move.quantity_done
                                move.product_uom_qty = n_shut * line_data.get('qty', 1)
                                move.unit_factor = line_data.get('qty', 1)
                                move.quantity_done = beforeOrdered
                                move._action_assign()
                                evaluatedMoves.append(move)
        # Materozza update
        materozzaMoves = [move for move in production.move_raw_ids if move not in evaluatedMoves]
        for materozzaMove in materozzaMoves:
            newQty = production.mold_id.product_raw_sprue_qty * n_shut
            materozzaMove.product_uom_qty = newQty
            materozzaMove._action_assign()

    @api.multi
    def change_prod_qty(self):
        for wizard in self:
            production = wizard.mo_id
            if production.state == 'external':
                self.change_prod_qty_external(production)
            elif production.mold_id:
                self.change_prod_qty_mold(production)
            else:
                super(ChangeProductionQty, self).change_prod_qty()
