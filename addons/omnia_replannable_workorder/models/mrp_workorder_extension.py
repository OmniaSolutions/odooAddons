# -*- encoding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, Open Source Management Solution    
#    Copyright (C) 2010-2011 OmniaSolutions (<http://www.omniasolutions.eu>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

'''
Created on May 16, 2018

@author: daniel
'''

from odoo import models
from odoo import fields
from odoo import api
from odoo import _


class MrpWorkorderExtension(models.Model):
    _name = 'mrp.workorder'
    _inherit = 'mrp.workorder'

    @api.one
    def checkMovesState(self):
        operationReplannable = self.operation_id.replannable
        if not operationReplannable:
            return 
        for line in self.raw_prod_ids:
            if line.state != 'assigned':
                self.has_to_be_checked = True
                return
        self.has_to_be_checked = False

    raw_prod_ids = fields.One2many('stock.move', inverse_name='replanning_raw_moves', string=_('Raw Moves'))
    has_to_be_checked = fields.Boolean(compute='checkMovesState', string="Check move states")

    def _generate_lot_ids(self):
        self.ensure_one()
        self.setupRawMaterials()
        return super(MrpWorkorderExtension, self)._generate_lot_ids()
        
    @api.one
    def setupRawMaterials(self):
        if not self.operation_id.replannable:
            return
        self.move_raw_ids.write({'replanning_raw_moves': self.id,
                                 'state': 'draft',
                                 })
#         rawRows = []
#         for moveBrws in self.move_raw_ids:
#             moveId = moveBrws.copy({'workorder_id': False}).id
#             if moveId:
#                 rawRows.append(moveId)
#         self.raw_prod_ids = [(6, 0, rawRows)]
#         self.move_raw_ids.action_cancel()
#         self.raw_prod_ids.write({'workorder_id': self.id})
        
    @api.multi
    def button_check_availability(self):
        for workOrderBrws in self:
            workOrderBrws.raw_prod_ids.action_confirm()
            workOrderBrws.raw_prod_ids.action_assign()
        