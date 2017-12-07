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
Created on 10 Apr 2017

@author: dsmerghetto
'''

from odoo import api
from odoo import fields
from odoo import models
from odoo import _


class ProductionWorcenter(models.Model):
    _inherit = 'mrp.workcenter.productivity'
 
    produced_qty = fields.Float(_('Produced Qty')) 


class MrpWorkOrder(models.Model):
    _inherit = 'mrp.workorder'
 
    @api.multi
    def record_production(self):
        
        producingQty = self.qty_producing
        res = super(MrpWorkOrder, self).record_production()
        if res:
            timeline_obj = self.env['mrp.workcenter.productivity']
            domain = [('workorder_id', 'in', self.ids), ('date_end', '=', False), ('user_id', '=', self.env.user.id)]
            timeLineObjs = timeline_obj.search(domain)
            if not timeLineObjs:
                domain = [('workorder_id', 'in', self.ids), ('user_id', '=', self.env.user.id)]
                timeLineObjs = timeline_obj.search(domain, order='date_end DESC')
            for timeline in timeLineObjs:
                if timeline.produced_qty == 0:
                    timeline.write({'produced_qty': producingQty})
                break
        if self.qty_remaining != 0:
            # These operations are needed when the process wizard is opened. This will split each instruction in a new timeline.
            self.end_previous() # End opened timeline
            return self.button_start()  # Start with a new timeline
        return True
    
    @api.multi
    def clientMachineRecordProduction(self, productedQty):
        for workOrder in self:
            if isinstance(productedQty, dict):
                lossReasonId = productedQty['id_loss_reason']
                desc = productedQty['description']
                timeline_obj = self.env['mrp.workcenter.productivity']
                self.end_previous()
                self.button_start()
                productivityBrwsList = timeline_obj.search([('workorder_id', 'in', self.ids), 
                                                            ('date_end', '=', False), 
                                                            ('user_id', '=', self.env.user.id)])
                for productivityBrws in productivityBrwsList:
                    productivityBrws.button_block()
                    productivityBrws.write({'date_end': False, 'loss_id': lossReasonId})
            elif workOrder.qty_produced + productedQty >= workOrder.qty_production:
                workOrder.record_production()
                workOrder.button_finish()
            else:
                workOrder.qty_producing = productedQty
                workOrder.record_production()
                
        return True
        
