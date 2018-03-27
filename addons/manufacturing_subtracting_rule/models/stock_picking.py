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
Created on Dec 18, 2017

@author: daniel
'''
from odoo import models
from odoo import api


class StockImmediateTransfer(models.TransientModel):
    _name = 'stock.immediate.transfer'
    _inherit = ['stock.immediate.transfer']

    @api.multi
    def process(self):
        '''
            Be sure to close the manufacturing order only if finished product is arrived.
        '''
        for objPick in self.pick_id:
            if self.isIncoming(objPick):
                maonOrder = self.getRelatedExternalManOrder(objPick)
                if not maonOrder:
                    continue
                self.createFinishedProducts(maonOrder)
                break
        res = super(StockImmediateTransfer, self).process()
        for objPick in self.pick_id:
            manufactObj = self.getRelatedExternalManOrder(objPick)
            if not manufactObj:
                continue
            if self.isOutGoing(objPick):
                self.doneManRawMaterials(manufactObj)
            elif self.isIncoming(objPick):
                self.removeMaterialFromSupplier(manufactObj)
                manufactObj.button_mark_done()
            break
        return res
        
    def doneManRawMaterials(self, manOrder):
        for lineBrws in manOrder.move_raw_ids:
            lineBrws.write({'state': 'done'})
        
    def getRelatedExternalManOrder(self, objPick):
        manufacturingObj = self.env['mrp.production']
        filterList = [('name', '=', objPick.origin),
                      ('state', '=', 'external')]
        for manufactObj in manufacturingObj.search(filterList):
            return manufactObj
        return None
        
    def isIncoming(self, objPick):
        if objPick.picking_type_id.code == 'incoming':
            return True
        return False
    
    def isOutGoing(self, objPick):
        if objPick.picking_type_id.code == 'outgoing':
            return True
        return False
        
    def removeMaterialFromSupplier(self, manufacturingObj):
        stockQuantObj = self.env['stock.quant']
        for consumedLineBrws in manufacturingObj.move_raw_ids:
            if consumedLineBrws.state == 'cancel':
                continue
            prodBrws = consumedLineBrws.product_id
            quantsForProduct = self.getStockQuant(stockQuantObj, consumedLineBrws.location_dest_id.id, prodBrws)
            for quantsForProductBrws in quantsForProduct:
                newQty = quantsForProductBrws.qty - consumedLineBrws.product_qty
                quantsForProductBrws.write({'qty': newQty})
                break

    def getStockQuant(self, stockQuantObj, lineId, prodBrws):
        quantsForProduct = stockQuantObj.search([
            ('location_id', '=', lineId),
            ('product_id', '=', prodBrws.id)
            ])
        return quantsForProduct
        
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
                    'product_id': prodBrws.id
                    })
            else:
                for quantsForProductBrws in quantsForProduct:
                    newQty = quantsForProductBrws.qty + finishedLineBrws.product_qty
                    quantsForProductBrws.write({'qty': newQty})
                    break
            
        