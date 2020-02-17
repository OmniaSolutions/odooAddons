# -*- encoding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, Your own solutions
#    Copyright (C) 2010 OmniaSolutions (<http://omniasolutions.eu>). All Rights Reserved
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
import os
import csv
import logging
import datetime
#
from openerp.exceptions import UserError
from openerp import models
from openerp import fields
from openerp import _
from openerp import osv
from openerp import api


class PlmDocument(models.Model):
    _inherit = 'plm.document'

    @api.multi
    def fix_workflows(self, model='plm.document', force_ids=[]):
        self.env['product.product'].fix_workflows(model=model, force_ids=force_ids)

