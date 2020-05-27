# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2010-2012 OpenERP s.a. (<http://openerp.com>).
#
#
#    Author : Smerghetto Daniel  (Omniasolutions)
#    mail:daniel.smerghetto@omniasolutions.eu
#    Copyright (c) 2014 Omniasolutions (http://www.omniasolutions.eu) 
#    All Right Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

'''
Created on Mar 27, 2018

@author: daniel
'''
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
import logging


class PurchaseOrder(models.Model):
    _name = "purchase.order"
    _inherit = ['purchase.order']

    production_external_id = fields.Many2one('mrp.production', string=_('External Production'))
    workorder_external_id = fields.Many2one('mrp.workorder', string=_('External Workorder'))

    # @api.multi
    def open_external_manufacturing(self):
        newContext = self.env.context.copy()
        manufacturingList = self.env['mrp.production'].browse()
        for purchaseLineBrws in self.order_line:
            manufacturingList = manufacturingList + purchaseLineBrws.production_external_id
        manufacturingIds = manufacturingList.ids
        return {
            'name': _("Manufacturing External"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'mrp.production',
            'type': 'ir.actions.act_window',
            'context': newContext,
            'domain': [('id', 'in', manufacturingIds)],
        }

    @api.depends('order_line.move_ids')
    def _compute_picking(self):
        super(PurchaseOrder, self)._compute_picking()
        for order in self:
            pickingsToAppend = self.env['stock.picking'].browse()
            for purchaseLineBrws in order.order_line:
                if purchaseLineBrws.production_external_id:
                    pickingsToAppend = pickingsToAppend + purchaseLineBrws.production_external_id.external_pickings
            order.picking_ids = order.picking_ids + pickingsToAppend
            order.picking_count = order.picking_count + len(pickingsToAppend)
