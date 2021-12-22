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
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import models
from odoo import api
from odoo import fields
from odoo import _
from odoo.exceptions import UserError
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
                if not order.analytic_account_id:
                    newBaseName = self.getNextAnalyticNumber()
                    newAnalyticAccount = order.createRelatedAnalyticAccount(newBaseName, order.partner_id)
                    if not newAnalyticAccount:
                        raise UserError(_('Unable to create analytic account!'))
                    newWarehouse = order.createRelatedWarehouse(newBaseName)
                    if not newWarehouse:
                        raise UserError(_('Unable to create warehouse!'))
                    order.analytic_account_id = newAnalyticAccount.id
                    order.warehouse_id = newWarehouse.id
                else:
                    newBaseName = order.analytic_account_id.name
                    if not order.warehouse_id:
                        order.warehouse_id = self.getRelatedWarehouse(newBaseName)
                if machinePresent:
                    order.setupAnalyticLines(newBaseName)
        res = super(SaleOrder, self).action_confirm()
        return res

    @api.multi
    def _create_analytic_account(self, prefix=None):
        '''
            Used to create account analytic account for service products and set as task
        '''
        orderName = self.getNextAnalyticNumber()
        for order in self:
            analytic = self.env['account.analytic.account'].create({
                'name': orderName,
                'code': order.client_order_ref,
                'company_id': order.company_id.id,
                'partner_id': order.partner_id.id
            })
            order.project_id = analytic

    @api.multi
    def getNextAnalyticNumber(self):
        newSequenceNumber = self.env['ir.sequence'].next_by_code('MATRICOLA')
        return str(date.today().year) + '/' + str(newSequenceNumber)

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
        if line.product_id and line.product_id.categ_id:
            return line.product_id.categ_id.with_context({'lang': 'en_US'}).name.upper()
        return ''

    @api.multi
    def setupAnalyticLines(self, newBaseName):
        count = 1
        for line in self.order_line:
            if self.getProductCategoryName(line) == 'MACHINE':
                for _elem in range(int(line.product_uom_qty)):
                    oldProdBrws = line.product_id
                    newProdBrws = self.createNewCodedProduct(newBaseName, count, oldProdBrws)
                    newSaleOrderLine = line.copy(default={'order_id': line.order_id.id})
                    newSaleOrderLine.product_id = newProdBrws.id
                    newSaleOrderLine.name = newSaleOrderLine.product_id.description_sale
                    self.moveOldBoms(oldProdBrws, newProdBrws)
                    newSaleOrderLine.product_uom_qty = 1.0
                    count = count + 1
                line.unlink()

    @api.multi
    def moveOldBoms(self, oldProdBrws, newProdBrws):
        for bomBrws in oldProdBrws.bom_ids:
            newBomBrws = bomBrws.copy()
            newBomBrws.product_tmpl_id = newProdBrws.product_tmpl_id
            newBomBrws.product_id = newProdBrws.id
        
    @api.multi
    def createNewCodedProduct(self, newBaseName, count, oldProdBrws):
        newProductName = str(newBaseName) + '/' + str('{:03.0f}'.format(count))
        toCreate = {
            'name': newProductName,
            'route_ids': [(6, False, self.getRoutesToSet())],
            'parent_product': oldProdBrws.product_tmpl_id.id,
            'description': '[%s] %s' % (oldProdBrws.name, oldProdBrws.description_sale or '-'),
            'description_sale': '[%s] %s' % (oldProdBrws.name, oldProdBrws.description_sale or '-')
            }
        try:
            return oldProdBrws.copy(oldProdBrws.id, toCreate)
        except:
            return oldProdBrws.copy(toCreate)
    
    @api.multi
    def getRoutesToSet(self):
        outIds = []
        routeEnv = self.env['stock.location.route']
        for elem in ['Make To Order', 'Manufacture']:
            routeBrws = routeEnv.with_context({'lang': 'en_US'}).search([
                ('name', '=', elem)])
            outIds.append(routeBrws.id)
        return outIds
    

