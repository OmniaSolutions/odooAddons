# -*- encoding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, Your own solutions
#    Copyright (C) 2010-2018 OmniaSolutions (<http://omniasolutions.eu>). All Rights Reserved
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
Created on Jul 25, 2018

@author: Daniel Smerghetto
'''
import logging
from datetime import datetime
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
from odoo.exceptions import ValidationError
from odoo.exceptions import AccessError
from odoo.exceptions import UserError
from odoo import osv
from odoo import SUPERUSER_ID
import os


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.model
    def _compute_obsoleted(self):
        for productionBrws in self:
            productionBrws.obsolete_presents =  productionBrws.bom_id.obsolete_presents or productionBrws.bom_id.obsolete_presents_recursive

    obsolete_presents = fields.Boolean(_("Obsolete presents"), compute='_compute_obsoleted')

    