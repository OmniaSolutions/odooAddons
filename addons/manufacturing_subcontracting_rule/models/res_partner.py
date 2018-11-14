# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2018-2018 OmniaSolutions (<http://omniasolutions.eu>)
#
#
#    Author : Matteo Boscolo  (Omniasolutions)
#    mail:matteo.boscolo@omniasolutions.eu
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
#    MERCHANTABILITY or Faddons.manufacturing_subcontracting_rule.modelsITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

'''
Created on Mar 27, 2018

@author: Matteo Boscolo
'''
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
import logging
import json


class ResPartner(models.Model):
    _inherit = ['res.partner']

    location_id = fields.Many2one('stock.location',
                                  'SubContracting Location',
                                  index=True,
                                  help="Sets a location if you produce at a fixed location. This can be a partner location if you subcontract the manufacturing operations.")

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        outArgs = []
        for fieldName, inner_operator, val in args:
            tmpOut = [fieldName, inner_operator, val]
            if inner_operator == 'in' and isinstance(val, (str, unicode)):
                try:
                    newVal = json.loads(val)
                    tmpOut[2] = newVal
                    operator = 'ilike'
                except Exception as ex:
                    logging.error(ex)
            outArgs.append(tmpOut)
        return super(ResPartner, self).name_search(name, outArgs, operator, limit)
