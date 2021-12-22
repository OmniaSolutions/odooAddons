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
Created on Jul 21, 2017

@author: daniel
'''
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import datetime
from odoo import models
from odoo import api
from odoo import fields
from odoo import _


class ManufacturingOrderOmnia(models.Model):
    _inherit = 'mrp.production'

    @api.onchange('product_id')
    def auto_reordering_rules_calculation(self):
        for mrp_production_id in self:
            self.env['procurement.order.omnia'].auto_reordering_rules_calculation(forceMrpBrws=[mrp_production_id])

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: