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
                    'quantity': finishedLineBrws.product_qty,
                    'location_id': finishedLineBrws.location_id.id,
                    'product_id': prodBrws.id})
            else:
                for quantsForProductBrws in quantsForProduct:
                    newQty = quantsForProductBrws.quantity + finishedLineBrws.product_qty
                    quantsForProductBrws.write({'quantity': newQty})
                    break

    def isIncoming(self):
        return self.sub_contracting_operation == 'close'

    def isOutGoing(self):
        return self.sub_contracting_operation == 'open'

    def doneManRawMaterials(self, manOrder):
        for lineBrws in manOrder.move_raw_ids:
            lineBrws.write({'state': 'done'})

    def removeMaterialFromSupplier(self, line, manufacturingObj, qty_produced):
        stockQuantObj = self.env['stock.quant']
        product_productObj = self.env['product.product']
        if line.state == 'cancel':
            return
        prodBrws = line.product_id
        for raw_bom in manufacturingObj.stock_bom_ids:
            if prodBrws.id == raw_bom.source_product_id:
                for product_id in product_productObj.browse(raw_bom.raw_product_id):
                    quantsForProduct = self.getStockQuant(stockQuantObj, line.location_id.id, product_id)
                    for quantsForProductBrws in quantsForProduct:
                        newQty = quantsForProductBrws.quantity - manufacturingObj.getQuantToRemove(product_id, qty_produced)
                        quantsForProductBrws.write({'quantity': newQty})
                        break

    def getStockQuant(self, stockQuantObj, lineId, prodBrws):
        quantsForProduct = stockQuantObj.search([
            ('location_id', '=', lineId),
            ('product_id', '=', prodBrws.id)])
        return quantsForProduct

    @api.multi
    def moveMaterialFromLine(self, line, remove=True):
        stockQuantObj = self.env['stock.quant']
        if line.state == 'cancel':
            return
        prodBrws = line.product_id
        quantsForProduct = self.getStockQuant(stockQuantObj, line.location_id.id, prodBrws)
        for quantsForProductBrws in quantsForProduct:
            out_qty = line.product_qty
            if remove:
                newQty = quantsForProductBrws.quantity - out_qty
            else:
                newQty = quantsForProductBrws.quantity + out_qty
            quantsForProductBrws.write({'quantity': newQty})
            return out_qty
        return 0.0

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

    def action_cancel(self):
        ref = super(StockPicking, self).action_cancel()
        if self.isIncoming():
            objProduction = self.env['mrp.production'].search([('id', '=', self.sub_production_id)])
            if objProduction.state == 'external' and objProduction.isPicksInDone():
                objProduction.button_mark_done()
        return ref
