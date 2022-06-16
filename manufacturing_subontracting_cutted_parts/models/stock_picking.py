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
#    Copyright (c) 2018 Omniasolutions (http://www.omniasolutions.eu)
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
Created on Dec 18, 2017

@author: daniel
'''
from odoo import models
from odoo import api
from odoo import fields
from odoo import _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        workorder = self.env['mrp.workorder']
        res = super(StockPicking, self).button_validate()
        if isinstance(res, dict) and res.get('type', '') == 'ir.actions.act_window':
            return res
        if self.isIncoming() and not self.isDropship():
            objProduction = self.env['mrp.production'].search([('id', '=', self.sub_production_id)])
            if objProduction and not objProduction.state == 'external':
                wh_out_dropship = self.checkDropship()
                if wh_out_dropship == self:
                    for stock_move_picking in self.move_lines:
                        if stock_move_picking.mrp_workorder_id:
                            workorder_id = workorder.browse(stock_move_picking.mrp_workorder_id)
                            if workorder_id.state == 'external' and stock_move_picking.product_id.row_material:
                                subcontract_finished_move = stock_move_picking.subcontractFinishedProduct()
                                stock_move_picking.subcontractRawProducts(subcontract_finished_move, objProduction)
                if objProduction.isPicksInDone():
                    objProduction.state = 'done'
            self.recomputePurchaseQty(self)
            self.cancel_other_partners_picks(self.partner_id, self.sub_production_id)
        return res
