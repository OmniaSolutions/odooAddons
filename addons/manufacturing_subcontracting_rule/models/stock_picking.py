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


class StockBackorderConfirmation(models.TransientModel):
    _name = 'stock.backorder.confirmation'
    _inherit = ['stock.backorder.confirmation']
    
    @api.multi
    def process(self):
        res = super(StockBackorderConfirmation, self).process()
        for objPick in self.pick_id:
            if objPick.isIncoming(objPick):
                objProduction = objPick.env['mrp.production'].search([('id', '=', objPick.sub_production_id)])
                if objProduction and objProduction.state == 'external':
                    for line in objPick.move_lines:
                        if line.mrp_production_id == objProduction.id and line.state == 'done':
                            line.subContractingProduce(objProduction)
                    if objProduction.isPicksInDone():
                        objProduction.button_mark_done()
        return res

    
class StockImmediateTransfer(models.TransientModel):
    _name = 'stock.immediate.transfer'
    _inherit = ['stock.immediate.transfer']

    @api.multi
    def process(self):
        res = super(StockImmediateTransfer, self).process()
        for objPick in self.pick_id:
            if objPick.isIncoming(objPick):
                objProduction = objPick.env['mrp.production'].search([('id', '=', objPick.sub_production_id)])
                if objProduction and objProduction.state == 'external':
                    for line in objPick.move_lines:
                        if line.mrp_production_id == objProduction.id and line.state == 'done':
                            line.subContractingProduce(objProduction)
                    if objProduction.isPicksInDone():
                        objProduction.button_mark_done()
        return res



class StockPicking(models.Model):
    _inherit = 'stock.picking'

    external_production = fields.Many2one('mrp.production')

    sub_contracting_operation = fields.Selection([('open', _('Open external Production')),
                                                  ('close', _('Close external Production'))])
    sub_production_id = fields.Integer(string=_('Sub production Id'))
    pick_out = fields.Many2one('stock.picking', string=_('Reference Stock pick out'))

    @api.multi
    def do_new_transfer(self):
        res = super(StockPicking, self).do_new_transfer()
        if isinstance(res, dict) and 'view_mode' in res:    # In this case will be returned a wizard
            return res
        for objPick in self:
            if objPick.isIncoming(objPick):
                objProduction = objPick.env['mrp.production'].search([('id', '=', objPick.sub_production_id)])
                if objProduction and objProduction.state == 'external':
                    for line in objPick.move_lines:
                        if line.mrp_production_id == objProduction.id:
                            line.subContractingProduce(objProduction)
                    if objProduction.isPicksInDone():
                        objProduction.button_mark_done()
        return res

#     @api.multi
#     def action_assign(self):
#         """In addition to what the method in the parent class does,
#         Changed batches states to assigned if all picking are assigned.
#         """
#         for objPick in self:
#             if self.isIncoming(objPick):
#                 maonOrder = self.getRelatedExternalManOrder(objPick)
#                 if not maonOrder:
#                     continue
#                 self.createFinishedProducts(maonOrder)
#                 break
#         return super(StockPicking, self).action_assign()

    def getRelatedExternalManOrder(self, objPick):
        manufacturingObj = self.env['mrp.production']
        filterList = [('name', '=', objPick.origin),
                      ('state', '=', 'external')]
        for manufactObj in manufacturingObj.search(filterList):
            return manufactObj
        return None

    def createFinishedProducts(self, manufacturingObj):
        stockQuantObj = self.env['stock.quant']
        for finishedLineBrws in manufacturingObj.move_finished_ids:
            if finishedLineBrws.state == 'cancel':  # Skip old lines
                continue
            prodBrws = finishedLineBrws.product_id
            quantsForProduct = self.getStockQuant(stockQuantObj, finishedLineBrws.location_id.id, prodBrws)
            if not quantsForProduct:
                stockQuantObj.create({
                    'qty': finishedLineBrws.product_qty,
                    'location_id': finishedLineBrws.location_id.id,
                    'product_id': prodBrws.id})
            else:
                for quantsForProductBrws in quantsForProduct:
                    newQty = quantsForProductBrws.qty + finishedLineBrws.product_qty
                    quantsForProductBrws.write({'qty': newQty})
                    break

    def isIncoming(self, objPick):
        return objPick.sub_contracting_operation == 'close'

    def isOutGoing(self, objPick):
        return objPick.sub_contracting_operation == 'open'

    def doneManRawMaterials(self, manOrder):
        for lineBrws in manOrder.move_raw_ids:
            lineBrws.write({'state': 'done'})

    def getStockQuant(self, stockQuantObj, lineId, prodBrws):
        quantsForProduct = stockQuantObj.search([
            ('location_id', '=', lineId),
            ('product_id', '=', prodBrws.id)])
        return quantsForProduct
