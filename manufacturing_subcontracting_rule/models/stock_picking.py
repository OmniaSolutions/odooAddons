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
    _name = 'stock.picking'
    _inherit = ['stock.picking']

    external_production = fields.Many2one('mrp.production')
    pick_out = fields.Many2one('stock.picking', string=_('Reference Stock pick out'))
    sub_contracting_operation = fields.Selection([('open', _('Open external Production')),
                                                  ('close', _('Close external Production'))])
    sub_production_id = fields.Integer(string=_('Sub production Id'))

    def isIncoming(self, objPick):
        return objPick.picking_type_code == 'incoming'

    def isOutGoing(self, objPick):
        return objPick.picking_type_code == 'outgoing'

    @api.multi
    def action_done(self):
        res = super(StockPicking, self).action_done()
        if self.isIncoming():
            objProduction = self.env['mrp.production'].search([('id', '=', self.sub_production_id)])
            if objProduction and objProduction.state == 'external':
                for line in self.move_lines:
                    if line.mrp_production_id == objProduction.id:
                        line.subContractingProduce(objProduction)
                if objProduction.isPicksInDone():
                    objProduction.button_mark_done()
        return res

    @api.multi
    def action_cancel(self):
        ref = super(StockPicking, self).action_cancel()
        for stock_picking in self:
            if stock_picking.isIncoming():
                objProduction = self.env['mrp.production'].search([('id', '=', stock_picking.sub_production_id)])
                if objProduction.state == 'external':
                    if objProduction.isPicksInDone():
                        objProduction.button_mark_done()
        return ref
