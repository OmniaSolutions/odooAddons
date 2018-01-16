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
Created on Sep 1, 2017

@author: daniel
'''
from openerp.exceptions import UserError
from openerp import models
from openerp import _
from openerp import api
from datetime import date

class stockpicking(models.Model):
    _name = "stock.picking"
    _inherit = "stock.picking"
    
    @api.model
    def create(self, vals):
        return super(stockpicking, self).create(vals)

class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = "sale.order"

    @api.multi
    def action_confirm(self):
        for order in self:
            machinePresent = self.checkMachineProductsPresents()
            machineNoProdPresent = False
            if not machinePresent:
                machineNoProdPresent = self.checkMachineProductsNoCreationPresents()
            if machinePresent or machineNoProdPresent:
                if not order.project_id:
                    newBaseName = self.getNextAnalyticNumber()
                    newAnalyticAccount = order.createRelatedAnalyticAccount(newBaseName, order.partner_id)
                    if not newAnalyticAccount:
                        raise UserError(_('Unable to create analytic account!'))
                    newWarehouse = order.createRelatedWarehouse(newBaseName)
                    if not newWarehouse:
                        raise UserError(_('Unable to create warehouse!'))
                    order.project_id = newAnalyticAccount.id
                    order.warehouse_id = newWarehouse.id
                else:
                    newBaseName = order.project_id.name
                    if not order.warehouse_id:
                        order.warehouse_id = self.getRelatedWarehouse(newBaseName)
                if machinePresent:
                    order.setupAnalyticLines(newBaseName)
        res = super(SaleOrder, self).action_confirm()
        return res

    @api.multi
    def getNextAnalyticNumber(self):
        newSequenceNumber = self.env['ir.sequence'].next_by_code('MATRICOLA')
        return unicode(date.today().year) + '/' + unicode(newSequenceNumber)

    @api.multi
    def createRelatedAnalyticAccount(self, newBaseName, partner_id):
        toCreate = {
            'name': newBaseName,
            'partner_id': partner_id.id,
            }
        return self.env['account.analytic.account'].create(toCreate)

    @api.multi
    def createRelatedWarehouse(self, newBaseName):
        toCreate = {
            'name': newBaseName,
            'code': newBaseName,
            }
        wareHouseBrws = self.env['stock.warehouse'].create(toCreate)
        return wareHouseBrws

    @api.multi
    def getRelatedWarehouse(self, name):
        for warehouseBrws in self.env['stock.warehouse'].search([('name', '=', name)]):
            return warehouseBrws.id
        return False

    @api.multi
    def checkMachineProductsNoCreationPresents(self):
        for line in self.order_line:
            if self.getProductCategoryName(line) == 'MACHINE NO PRODUCT':
                return True
        return False

    @api.multi
    def checkMachineProductsPresents(self):
        for line in self.order_line:
            if self.getProductCategoryName(line) == 'MACHINE':
                return True
        return False

    @api.multi
    def getProductCategoryName(self, line):
        return line.product_id.categ_id.with_context({'lang': 'en_US'}).name.upper()

    @api.multi
    def setupAnalyticLines(self, newBaseName):
        count = 1
        for line in self.order_line:
            if self.getProductCategoryName(line) == 'MACHINE':
                for _elem in range(int(line.product_uom_qty)):
                    newProdBrws = self.createNewCodedProduct(newBaseName, count, line.product_id)
                    newSaleOrderLine = line.copy(default={'order_id': line.order_id.id})
                    newSaleOrderLine.product_id = newProdBrws.id
                    newSaleOrderLine.product_uom_qty = 1.0
                    count = count + 1
                line.unlink()
        
    @api.multi
    def createNewCodedProduct(self, newBaseName, count, oldProdBrws):
        newProductName = unicode(newBaseName) + '/' + unicode('{:03.0f}'.format(count))
        toCreate = {
            'name': newProductName,
            'route_ids': [(6, False, self.getRoutesToSet())],
            'parent_product': oldProdBrws.product_tmpl_id.id,
            }
        return oldProdBrws.copy(default=toCreate)
    
    @api.multi
    def getRoutesToSet(self):
        outIds = []
        routeEnv = self.env['stock.location.route']
        for elem in ['Make To Order', 'Manufacture']:
            routeBrws = routeEnv.with_context({'lang': 'en_US'}).search([
                ('name', '=', elem)])
            outIds.append(routeBrws.id)
        return outIds
    

