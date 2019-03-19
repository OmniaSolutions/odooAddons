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
Created on Mar 22, 2018

@author: daniel
'''

from odoo import models
from odoo import fields
from odoo import api
from odoo import _
import logging
import datetime


class SaleOrderExtension(models.Model):

    _name = "sale.order"
    _inherit = ['sale.order']
    
    @api.multi
    def action_confirm(self):
        if self.checkProdOrderProducts():
            warehouseBrws = self.createProdOrderWarehouse()
            self.write({'warehouse_id': warehouseBrws.id,
                        'project_id': warehouseBrws.project_id.id
                        })
            if self.checkIfModuleInstalled('omnia_sale_reordering_rule'):
                self.checkLinesReorder()
        return super(SaleOrderExtension, self).action_confirm()
    
    @api.multi
    def createProdOrderWarehouse(self):
        name = '%s-%s' % (self.name, self.env['ir.sequence'].next_by_code('SALE_PROD_ORDER'))
        toCreate = {
            'name': name,
            'code': name,
            }
        wareHouseBrws = self.env['stock.warehouse'].create(toCreate)
        return wareHouseBrws

    @api.model
    def checkIfModuleInstalled(self, moduleName):
        moduleBrwsList = self.sudo().env['ir.module.module'].search([('name', '=', moduleName)])
        for modbrws in moduleBrwsList:
            if modbrws.state == 'installed':
                return True
        return False

    def checkProdOrderProducts(self):
        for lineBrws in self.order_line:
            prodBrws = lineBrws.product_id
            if prodBrws:
                tmplBrws = prodBrws.product_tmpl_id
                if tmplBrws.production_order_use:
                    return True
        return False
        