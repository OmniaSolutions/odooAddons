# -*- coding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, ERP-PLM-CAD Open Source Solutions
#    Copyright (C) 2011-2019 https://OmniaSolutions.website
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
#    along with this prograIf not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
'''
Created on Aug 9, 2019

@author: mboscolo
'''
import logging
import datetime
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
from odoo.exceptions import UserError
from datetime import timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class IrAttachment(models.Model):
    _name = ""
    _inherit = ['ir.attachment']

    tipo_mrp = fields.Char(string="Tipo Mrp")
    ir_attachment_relation = fields.Many2many(relation="mrp_routing_workcenter_ir_attachment",
                                              comodel_name='mrp.routing.workcenter',
                                              column2="mrp_id",
                                              column1="attachemnt_id")

    @api.multi
    def download_document(self):
        return {
            'type': 'ir.actions.act_url',
            'name': 'contract',
            'url': '/web/content/%s?download=true' % (self.id),
        }
