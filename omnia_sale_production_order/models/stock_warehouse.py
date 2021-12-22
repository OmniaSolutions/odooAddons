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


class StockWarehouseExtension(models.Model):

    _name = "stock.warehouse"
    _inherit = ['stock.warehouse']

    project_id = fields.Many2one(comodel_name='project.project', string=_('Project'))

    @api.model
    @api.returns('self', lambda value:value.id)
    def create(self, vals):
        warehouseCode = vals.get('code', '')
        if not vals.get('project_id'):
            pojBrws = self.createProject(warehouseCode)
            vals['project_id'] = pojBrws.id
        return super(StockWarehouseExtension, self).create(vals)
    
    def createProject(self, code):
        toCreate = {
            'name': code,
            }
        projProjBrws = self.env['project.project'].create(toCreate)
        return projProjBrws
